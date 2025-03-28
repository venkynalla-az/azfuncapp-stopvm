from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError

import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def stop_vm(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(
        "Python HTTP trigger function to stop a VM processed a request.")

    # Retrieve query parameters
    subscription_id = req.params.get("subscription_id")
    resource_group = req.params.get('resource_group')
    vm_name = req.params.get('vm_name')

    if not subscription_id or not resource_group or not vm_name:
        return func.HttpResponse(
            "Please provide subscription_id, resource_group, and vm_name as query parameters.",
            status_code=400
        )

    try:
        # Create a default Azure credential (e.g., from environment or Managed Identity)
        credential = DefaultAzureCredential()

        # Create the Compute Management client
        compute_client = ComputeManagementClient(credential, subscription_id)
        instance_state = compute_client.virtual_machines.instance_view(
            resource_group, vm_name)
        vm_states = []

        for status in instance_state.statuses:
            vm_states.append(status.code)

        if "PowerState/running" in vm_states:
            # Stop the VM
            logging.info(
                f"Virtual machine: {vm_name} in resource group: {resource_group} is running. Stopping it now...")            
            async_vm_stop = compute_client.virtual_machines.begin_deallocate(
                resource_group, vm_name)
            async_vm_stop.result()  # Wait for the VM to stop
            return func.HttpResponse(f"Successfully Stopped (deallocated) VM: {vm_name}", status_code=200)
        else:
            logging.info(
                f"Virtual machine: {vm_name} in resource group: {resource_group} is not running.")
            return func.HttpResponse(f"Virtual machine: {vm_name} is not running.", status_code=200)

    except ResourceNotFoundError:
        return func.HttpResponse(f"VM: {vm_name} not found in resource group: {resource_group}", status_code=404)

    except Exception as e:
        logging.error(f"Error stopping the VM: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
