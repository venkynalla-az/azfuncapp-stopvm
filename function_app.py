from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError

import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="http_trigger")
def start_vm(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(
        "Python HTTP trigger function to start a VM processed a request.")

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
        #credential = DefaultAzureCredential()
        credential = ClientSecretCredential("60943e68-a81c-460d-a797-6cf9d649f2ec", "26df0f3c-dde6-41cd-ac37-f4e3352491d7", "s2z8Q~sBdfIUCy.3tEF-Uy5EzvFXJUs-4XPFAbfk")

        # Create the Compute Management client
        compute_client = ComputeManagementClient(credential, subscription_id)
        instance_state = compute_client.virtual_machines.instance_view(
            resource_group, vm_name)
        vm_states = []

        for status in instance_state.statuses:
            vm_states.append(status.code)

        if "PowerState/deallocated" in vm_states:
            # Start the VM
            logging.info(
                f"Virtual machine: {vm_name} in resource group: {resource_group} is stopped. Starting it now...")
            async_vm_start = compute_client.virtual_machines.begin_start(
                resource_group, vm_name)
            async_vm_start.result()  # Wait for the VM to start
            return func.HttpResponse(f"Successfully started VM: {vm_name}", status_code=200)
        else:
            logging.info(
                f"Virtual machine: {vm_name} in resource group: {resource_group} appears to be running.")
            return func.HttpResponse(f"Virtual machine: {vm_name} appears to be running.", status_code=200)

    except ResourceNotFoundError:
        return func.HttpResponse(f"VM: {vm_name} not found in resource group: {resource_group}", status_code=404)

    except Exception as e:
        logging.error(f"Error starting the VM: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
