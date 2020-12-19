from azureml.core import Workspace, Dataset, Datastore, Experiment, Environment
from azureml.core.compute import AmlCompute
from azureml.core.runconfig import RunConfiguration
from azureml.core.conda_dependencies import CondaDependencies
from azureml.pipeline.core import Pipeline, PipelineData
from azureml.pipeline.steps import PythonScriptStep
import json
import sys

########## General info about our Azure instance ##########
with open("settings.json") as f:
    settings = json.load(f)

########## Data prep stuff ##########
dataprep_source_dir = "./dataprep_src"
entry_point = "prepare.py"

########## Training stuff ##########
train_source_dir = "./train_src"
train_entry_point = "train.py"

if __name__ == "__main__":
    compute_target = None
    workspace = Workspace(settings["subscription_id"], settings["resource_group"], settings["workspace_name"])
    if settings["compute_name"] in workspace.compute_targets:
        compute_target = workspace.compute_targets[settings["compute_name"]]
        if compute_target and type(compute_target) is AmlCompute:
            print("Found compute target: " + settings["compute_name"])
        else:
            print("Unable to find compute target: " + settings["compute_name"], file=sys.stderr, flush=True)
            exit(1)

    dataset = Dataset.get_by_name(workspace, name="Discord")
    # dataset.download(target_path=".", overwrite=False)
    blob_store = Datastore(workspace, "workspaceblobstore")
    aml_run_config = RunConfiguration()
    aml_run_config.target = compute_target
    curated_environment = Environment.get(workspace=workspace, name="AzureML-AutoML-GPU")
    aml_run_config.environment = curated_environment

    ########## We"re done with setup, time to do the actual job

    # Step 1: Prepare our data for consumption

    prepared_data = PipelineData("prepared_data", datastore=blob_store)

    ds_input = dataset.as_named_input("input1")

    data_prep_step = PythonScriptStep(
        script_name=entry_point,
        source_directory=dataprep_source_dir,
        arguments=["--input", ds_input.as_download(), "--output", prepared_data],
        inputs=[ds_input],
        outputs=[prepared_data],
        compute_target=compute_target,
        runconfig=aml_run_config,
        allow_reuse=True
    )

    # Step 2: Train our model
    training_results = PipelineData(name = "training_results", datastore=blob_store)

    train_step = PythonScriptStep(
        script_name=train_entry_point,
        source_directory=train_source_dir,
        arguments=["--prepped_data", prepared_data.as_input(), "--training_results", training_results],
        compute_target=compute_target,
        runconfig=aml_run_config,
        allow_reuse=True
    )

    # Step 3: Build the pipeline
    pipeline_steps = [data_prep_step, train_step]
    pipeline = Pipeline(workspace=workspace, steps=[pipeline_steps])

    pipeline_run1 = Experiment(workspace, "mckee_bot").submit(pipeline)
    pipeline_run1.wait_for_completion()