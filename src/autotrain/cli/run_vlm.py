from argparse import ArgumentParser

from autotrain import logger
from autotrain.cli.utils import get_field_info, vlm_munge_data
from autotrain.project import AutoTrainProject
from autotrain.trainers.vlm.params import VLMTrainingParams

from . import BaseAutoTrainCommand


def run_vlm_command_factory(args):
    return RunAutoTrainVLMCommand(args)


class RunAutoTrainVLMCommand(BaseAutoTrainCommand):
    @staticmethod
    def register_subcommand(parser: ArgumentParser):
        arg_list = get_field_info(VLMTrainingParams)
        arg_list = [
            {
                "arg": "--train",
                "help": "Command to train the model",
                "required": False,
                "action": "store_true",
            },
            {
                "arg": "--deploy",
                "help": "Command to deploy the model (limited availability)",
                "required": False,
                "action": "store_true",
            },
            {
                "arg": "--inference",
                "help": "Command to run inference (limited availability)",
                "required": False,
                "action": "store_true",
            },
        ] + arg_list
        run_image_regression_parser = parser.add_parser("vlm", description="✨ Run AutoTrain VLM")
        for arg in arg_list:
            if "action" in arg:
                run_image_regression_parser.add_argument(
                    arg["arg"],
                    help=arg["help"],
                    required=arg.get("required", False),
                    action=arg.get("action"),
                    default=arg.get("default"),
                )
            else:
                run_image_regression_parser.add_argument(
                    arg["arg"],
                    help=arg["help"],
                    required=arg.get("required", False),
                    type=arg.get("type"),
                    default=arg.get("default"),
                    choices=arg.get("choices"),
                )
        run_image_regression_parser.set_defaults(func=run_vlm_command_factory)

    def __init__(self, args):
        self.args = args

        store_true_arg_names = [
            "train",
            "deploy",
            "inference",
            "auto_find_batch_size",
            "push_to_hub",
        ]
        for arg_name in store_true_arg_names:
            if getattr(self.args, arg_name) is None:
                setattr(self.args, arg_name, False)

        if self.args.train:
            if self.args.project_name is None:
                raise ValueError("Project name must be specified")
            if self.args.data_path is None:
                raise ValueError("Data path must be specified")
            if self.args.model is None:
                raise ValueError("Model must be specified")
            if self.args.push_to_hub:
                if self.args.username is None:
                    raise ValueError("Username must be specified for push to hub")
        else:
            raise ValueError("Must specify --train, --deploy or --inference")

        if self.args.backend.startswith("spaces") or self.args.backend.startswith("ep-"):
            if not self.args.push_to_hub:
                raise ValueError("Push to hub must be specified for spaces backend")
            if self.args.username is None:
                raise ValueError("Username must be specified for spaces backend")
            if self.args.token is None:
                raise ValueError("Token must be specified for spaces backend")

    def run(self):
        logger.info("Running Image Regression")
        if self.args.train:
            params = VLMTrainingParams(**vars(self.args))
            params = vlm_munge_data(params, local=self.args.backend.startswith("local"))
            project = AutoTrainProject(params=params, backend=self.args.backend)
            job_id = project.create()
            logger.info(f"Job ID: {job_id}")
