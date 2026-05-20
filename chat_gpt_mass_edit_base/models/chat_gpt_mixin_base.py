import base64
import importlib
import json
import logging
import re

import requests

from odoo import _, api
from odoo.exceptions import AccessError, UserError
from odoo.models import BaseModel

from odoo.addons.iap.tools import iap_tools

DEFAULT_LIBRARY_ENDPOINT = "https://media-api.odoo.com"
DEFAULT_OLG_ENDPOINT = "https://olg.api.odoo.com"

_logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI, BadRequestError, OpenAI
except ImportError as e:
    _logger.warning(e)
    _logger.warning("For advanced features openai is needed.")


class ChatGPTMixinBase:
    """
    The Methods for the mixin are in this model because they are identical for Models and Transient Models.
    To avoid Code duplication, the methods are inherited from both.
    """

    _name = "chat_gpt_mass_edit_base.mixin.base"
    _description = "ChatGPT Mixin Base"
    _module = "mytime_official.chat_gpt_mass_edit_base"

    def default_gpt_field_to_map_image(self):
        if field_id := self.env["ir.model.fields"].search(
            [
                ("model_id", "=", self.res_model_id.id),
                ("ttype", "=", "binary"),
                ("store", "=", True),
                ("readonly", "=", False),
            ],
            limit=1,
        ):
            return field_id
        else:
            return False

    def _compute_gpt_field_to_map_image(self):
        for record in self:
            image_field_id = self.env["ir.model.fields"].search(
                [
                    ("model_id", "=", self.res_model_id.id),
                    ("ttype", "=", "binary"),
                    ("store", "=", True),
                    ("readonly", "=", False),
                ],
                limit=1,
            )
            record.gpt_field_to_map_image = image_field_id

    def query_chat_gpt(self):
        for record in self:
            answer = record._get_chatgpt_response(record.gpt_question)
            record.gpt_answer = answer
            if record.gpt_field_to_map_answer:
                setattr(record, record.gpt_field_to_map_answer.name, answer)

    def query_chat_gpt_with_odoo(self, prompt):
        try:
            irconfigparameter = self.env["ir.config_parameter"].sudo()
            olg_api_endpoint = irconfigparameter.get_param("web_editor.olg_api_endpoint", DEFAULT_OLG_ENDPOINT)
            database_id = irconfigparameter.get_param("database.uuid")
            response = iap_tools.iap_jsonrpc(
                f"{olg_api_endpoint}/api/olg/1/chat",
                params={
                    "prompt": prompt,
                    "conversation_history": [],
                    "database_id": database_id,
                },
                timeout=30,
            )
            if response["status"] == "success":
                return response["content"]
            elif response["status"] == "error_prompt_too_long":
                raise UserError(_("Sorry, your prompt is too long. Try to say it in fewer words."))
            elif response["status"] == "limit_call_reached":
                raise UserError(
                    _("You have reached the maximum number of requests for this service. Try again later.")
                )  # noqa: B904
            else:
                raise UserError(_("Sorry, we could not generate a response. Please try again later."))
        except AccessError as e:
            raise AccessError(_("Oops, it looks like our AI is unreachable!")) from e

    def get_model_name(self):
        params = self.env["ir.config_parameter"].sudo()
        model_id = params.get_param("chat_gpt_mass_edit_base.chatgpt_model_id")
        if model_id:
            return self.env["chatgpt.model"].browse(int(model_id)).name
        return "gpt-4o"

    def get_client(self):
        params = self.env["ir.config_parameter"].sudo()
        org_id = params.get_param("chat_gpt_mass_edit_base.org_id")
        project = params.get_param("chat_gpt_mass_edit_base.project")
        openapi_api_key = params.get_param("chat_gpt_mass_edit_base.openapi_api_key")
        if importlib.util.find_spec("openai") is None:
            raise UserError(
                _(
                    "To use this feature it's necessary to install the openai package in python. "
                    "But you can continue with the odoo standard API "
                    "if you switch it back in the settings -> ChatGPT."
                )
            )
        return OpenAI(organization=org_id, project=project, api_key=openapi_api_key)

    def get_async_client(self):
        params = self.env["ir.config_parameter"].sudo()
        org_id = params.get_param("chat_gpt_mass_edit_base.org_id")
        project = params.get_param("chat_gpt_mass_edit_base.project")
        openapi_api_key = params.get_param("chat_gpt_mass_edit_base.openapi_api_key")
        if importlib.util.find_spec("openai") is None:
            raise UserError(
                _(
                    "To use this feature it's necessary to install the openai package in python. "
                    "But you can continue with the odoo standard API "
                    "if you switch it back in the settings -> ChatGPT."
                )
            )
        return AsyncOpenAI(organization=org_id, project=project, api_key=openapi_api_key)

    def replace_placeholders(self, record):  # NOSONAR
        placeholders = re.findall(r"{(\w+)}", record.gpt_question_template)
        result = record.gpt_question_template

        for placeholder in placeholders:
            try:
                # there is a feature that variables with
                # {block_xxx} get rendered so this is no error
                if "block_" not in placeholder:
                    replace_with = getattr(record, placeholder)
                    if isinstance(replace_with, BaseModel):
                        replace_with = replace_with.name
                    if replace_with:
                        result = result.replace(f"{{{placeholder}}}", replace_with)
                    else:
                        continue
            except AttributeError:
                result = result.replace(f"{{{placeholder}}}", "False")

                record.error_message += f"Field: {placeholder} not found in model: {record.res_model_id.model}\n"
            except Exception as e:
                _logger.warning(e)

            block_info_json = {"name": record.name, "background": "plane, grey"}
            block_attributes = ""
            if record.res_model_id.model == "product.product":
                values_display = []
                for value_id in record.product_template_variant_value_ids:
                    if value_id.attribute_id.name in block_info_json:
                        block_info_json[value_id.attribute_id.name].append(value_id.name)
                    else:
                        block_info_json[value_id.attribute_id.name] = value_id.name
                    values_display.append(f" {value_id.display_name} ")

                block_attributes = "".join(values_display)

            elif record.res_model_id.model == "product.template":
                attributes_strings = []
                for al in record.attribute_line_ids:
                    attributes_strings.extend(value_id.display_name for value_id in al.value_ids)

                    for value_id in al.value_ids:
                        if value_id.attribute_id.name in block_info_json:
                            block_info_json[value_id.attribute_id.name].append(value_id.name)

                        else:
                            block_info_json[value_id.attribute_id.name] = [value_id.name]
                block_attributes = " ".join(attributes_strings)
            if result:
                result = result.replace("{block_attributes}", block_attributes)
                try:
                    extra_info = json.loads(record.json_extra_info)
                except Exception as e:
                    _logger.warning(e)
                    raise UserError(
                        _("There is a problem with the json string: %(json_extra_info)s")
                        % {"json_extra_info": record.json_extra_info}
                    ) from e
                block_attributes = block_info_json.update(extra_info)
                result = result.replace("{block_info_json}", json.dumps(block_info_json))
        return result

    @api.depends("gpt_question_template")
    def _compute_gpt_question_wizard(self):
        for record in self:
            if not record._transient:
                if record.gpt_question_template:
                    record_model = record.env[record.res_model_id.model].browse(record.sample_product_template_id)
                    record_model.gpt_question_template = record.gpt_question_template
                    record_model.json_extra_info = record.json_extra_info
                    record.gpt_question = self.replace_placeholders(record_model)
                else:
                    record.gpt_question = False

    @api.depends("gpt_question_template")
    def _compute_gpt_question_model(self):
        for record in self:
            if not record._transient:
                if record.gpt_question_template:
                    record.gpt_question = self.replace_placeholders(record)
                else:
                    record.gpt_question = False

    def get_sync_completion(self, base64_image, system_message, user_message, output_format="json"):
        response = self.get_client().chat.completions.create(
            model=self.get_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": system_message,
                },  # "You are a helpful assistant that responds in json"
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message,
                        },  # "What's the area of the triangle?"
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                },
            ],
            temperature=0.0,
        )

        result = response.choices[0].message.content
        if output_format == "json":
            result = json.loads(result)
        return result

    async def _get_image_from_chatgpt(self, prompt, kwargs=None):
        if kwargs is None:
            kwargs = {}
        model = kwargs.get("model", "dall-e-3")
        n = kwargs.get("n", 1)
        quality = kwargs.get("quality", "standard")
        size = kwargs.get("size", "1024x1024")

        try:
            response = await self.get_async_client().images.generate(
                model=model,
                prompt=prompt,
                n=n,  # Number of images to generate
                quality=quality,
                size=size,  # Image size: 256x256, 512x512, or 1024x1024
            )
        except BadRequestError as e:
            raise UserError(e.message) from e
        except Exception as e:
            _logger.warning(e)

        # Get the image URL
        image_url = response.data[0].url

        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for bad responses

        return base64.b64encode(response.content)

    def _get_chatgpt_response(self, prompt, base64_image=None, system_message=None, output_format="json"):
        ICP = self.env["ir.config_parameter"].sudo()
        if not ICP.get_param("chat_gpt_mass_edit_base.use_odoo_default"):
            return (
                self.get_sync_completion(
                    base64_image,
                    system_message,
                    prompt,
                    output_format=output_format,
                )
                if base64_image
                else self._use_custom_chatgpt(prompt)
            )
        if base64_image:
            raise UserError(
                _(
                    "You choose the odoo default chatgpt, you can not use images. "
                    "Please add your own chatgpt developer account in the settings"
                    " to use this feature."
                )
            )
        return self.query_chat_gpt_with_odoo(prompt)

    def _use_custom_chatgpt(self, prompt):
        ICP = self.env["ir.config_parameter"].sudo()
        api_key = ICP.get_param("chat_gpt_mass_edit_base.openapi_api_key")
        if not api_key:
            raise UserError(_("There is no api key supplied"))
        gpt_model_id = ICP.get_param("chat_gpt_mass_edit_base.chatgpt_model_id")
        gpt_model = "gpt-4o"
        try:
            if gpt_model_id:
                gpt_model = self.env["chatgpt.model"].browse(int(gpt_model_id)).name
        except Exception:
            gpt_model = "gpt-4o"
        try:
            if importlib.util.find_spec("openai") is None:
                raise UserError(_("To use this feature it's necessary to install the openai package in python."))
            client = OpenAI(api_key=api_key)
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(messages=messages, model=gpt_model, temperature=0.0)
            return response.choices[0].message.content
        except UserError as e:
            _logger.warning(e)
            raise e from e
        except Exception as e:
            _logger.warning(e)
            raise e from e
