import asyncio
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

GENERAL_PROMPTS = """Only use html markup, never markdown or others. Don't use ```html ```
    Don't use placeholders the text should be ready as is.
    Answer only with the description for an online shop.
    The size should be about 100 words. """

DEFAULT_EXTRA_PROMT = {
    "question": GENERAL_PROMPTS,
    "image": GENERAL_PROMPTS,
    "create_image": ("use a plain neutral background."),
}

DEFAULT_PROMPT = {
    "question": ("Create a short summary for the product {name}. In the category {categ_id}. "),
    "image": (
        "Can you create a product description for an webshop from the attached image? "
        "The title is {name} and it's a {categ_id}. "
    ),
    "create_image": ("Create an image for the product {block_info_json}. "),
}


class ChatGPTMassEdit(models.TransientModel):
    _name = "gpt_wizard"
    _inherit = ["chat_gpt_mass_edit_base.transient.mixin"]
    _description = "Create Mass Edits of ChatGPT promts"

    error_message = fields.Text(readonly=True)
    advanced_settings = fields.Boolean()

    system_message = fields.Text(compute="_compute_system_message", store=True)

    old_type_of_prompt = fields.Char()

    type_of_prompt = fields.Selection(
        selection=[
            ("question", "Dynamic Question to field"),
            ("image", "Image Analysis"),
            ("create_image", "Create Image"),
        ],
        string="Type of Prompt",
        default="question",
    )

    image_size = fields.Selection(
        selection=[
            ("256x256", "256x256"),
            ("512x512", "512x512"),
            ("1024x1024", "1024x1024"),
        ],
        default="1024x1024",
    )

    image_quality = fields.Selection(
        selection=[
            ("standard", "standard"),
        ],
        default="standard",
    )
    image_model = fields.Selection(
        selection=[
            ("dall-e-3", "dall-e-3"),
        ],
        default="dall-e-3",
    )

    add_image_to_extra_images = fields.Boolean(default=True)

    gpt_extra_template = fields.Char(compute="_compute_gpt_extra_template", store=True, readonly=False)

    # the model is generally stored but if the type is changed we want to preselect the field
    # so the user don't has to select the image in product.product or product.template
    gpt_field_to_map_image = fields.Many2one(readonly=False, compute="_compute_gpt_field_to_map_image")  #

    json_extra_info = fields.Char(default='{"background": "plane, gray", "style": "comic"}')

    @api.depends("type_of_prompt")
    def _compute_gpt_extra_template(self):
        for record in self:
            record.gpt_extra_template = DEFAULT_EXTRA_PROMT.get(record.type_of_prompt, "")

    @api.depends("type_of_prompt")
    def _compute_system_message(self):
        for record in self:
            default_system_message = (
                f"Answer right with the content. "
                f"The language should be {record.current_lang}. "
                "Only use html markup, never markdown or others. "
                "Don't use placeholders the text should be ready as is. "
            )

            if record.type_of_prompt == "image":
                record.system_message = f"{default_system_message} Include the image in your answer."
            elif record.type_of_prompt == "question":
                record.system_message = default_system_message
            else:
                record.system_message = default_system_message

    @api.model
    def _lang_get(self):
        return self.env["res.lang"].get_installed()

    lang = fields.Selection(string="Target Language", selection=_lang_get, store=True)
    current_lang = fields.Selection(
        string="Current Language",
        help=(
            "is the current language of the user. "
            "If you want to translate a different language change the user language to the source language."
        ),
        selection=_lang_get,
        readonly=True,
    )

    # should be auto filled if "create_image" is selected
    # pylint: disable=W8110
    @api.depends("type_of_prompt")
    def _compute_gpt_field_to_map_image(self):
        super()._compute_gpt_field_to_map_image()

    # pylint: disable=W8110    # pylint: disable=W8110
    @api.depends("gpt_question_template", "type_of_prompt")
    def _compute_gpt_question_wizard(self):  # NOSONAR
        super()._compute_gpt_question_wizard()
        for record in self:
            if record.type_of_prompt != record.old_type_of_prompt:
                # if the type is changed the default prompt is restored.
                record.gpt_question_template = DEFAULT_PROMPT.get(record.type_of_prompt, "")
                # + (f" The language should be {record.current_lang}. ")
                record.old_type_of_prompt = record.type_of_prompt
            if record.type_of_prompt in ["question", "image", "create_image"]:
                record.error_message = ""
                if record._transient:
                    if record.gpt_question_template:
                        record_model = record.env[record.res_model_id.model].browse(
                            record.sample_product_template_id
                        )
                        record_model.gpt_question_template = self.gpt_question_template
                        record_model.json_extra_info = record.json_extra_info
                        modified_template = self.replace_placeholders(record_model)
                        record.gpt_question = (
                            modified_template + record.gpt_extra_template
                            if record.gpt_extra_template
                            else modified_template
                        )
                    else:
                        record.gpt_question = False

    async def get_results_from_gpt_wizard_async(self, records):
        tasks = []
        tasks.extend(self.inner_function_async(record) for record in records)
        await asyncio.gather(*tasks)

    async def inner_function_async(self, record):
        await self.inner_function(record)
        # await asyncio.to_thread(self.inner_function(record))

    async def inner_function(self, record):
        record.gpt_question_template = self.gpt_question_template
        record.json_extra_info = self.json_extra_info
        record._compute_gpt_question_model()
        base64_image = getattr(record, self.gpt_field_for_input_image.name)

        if self.type_of_prompt == "create_image":
            base64_image = await self._get_image_from_chatgpt(
                record.gpt_question,
                {
                    "model": self.image_model,
                    "n": 1,
                    "quality": self.image_quality,
                    "size": self.image_size,
                },
            )
            if self.gpt_field_to_map_image:
                setattr(record, self.gpt_field_to_map_image.name, base64_image)

            if self.add_image_to_extra_images:
                file_name = "image_from_dalle"

                if record._name == "product.template":
                    self.env["product.image"].create(
                        {"name": file_name, "image_1920": base64_image, "product_tmpl_id": record.id}
                    )
                elif record._name == "product.product":
                    self.env["product.image"].create(
                        {"name": file_name, "image_1920": base64_image, "product_variant_id": record.id}
                    )

        if base64_image and self.type_of_prompt == "image":
            base64_image = base64_image.decode("utf-8")
        else:
            base64_image = None
        answer = self._get_chatgpt_response(
            record.gpt_question,
            base64_image=base64_image,
            system_message=self.system_message,
            output_format="text",
        )
        if self.gpt_field_to_map_answer:
            setattr(record, self.gpt_field_to_map_answer.name, answer)

    def get_results_from_gpt_wizard(self):
        ids = self.res_model_IDS.split(",")
        model__ids = [int(id) for id in ids]
        records = self.env[self.res_model_id.model].browse(model__ids)

        asyncio.run(self.get_results_from_gpt_wizard_async(records))
