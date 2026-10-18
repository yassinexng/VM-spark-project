import subprocess, json, os
from dotenv import set_key, dotenv_values, load_dotenv
import time

logged_in = True

if not logged_in:
    login_cmd = ["az", "login"]
    com1 = subprocess.run(
        login_cmd,
        capture_output=True,
    )


def get_data():
    # Ensure .env exists so set_key does not fail
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            pass

    vm_list = ["az", "vm", "list"]
    com2 = subprocess.run(
        vm_list,
        capture_output=True,
        text=True,
    )
    if not com2.stdout.strip():
        return f"Error: az vm list returned empty output. Check Azure login."

    com2_json = json.loads(com2.stdout)
    if not com2_json:
        return "Error: No VMs found in the subscription."

    id = com2_json[0]["id"]
    location = com2_json[0].get("location", "")
    values = id.split("/")
    subscription = values[2]
    ressource_group = values[4]
    one_vm = True
    data = {
        "subscription": subscription,
        "ressource-group": ressource_group,
        "location": location,
    }
    if one_vm:
        vm_name = values[len(values) - 1]
        data["vm-name"] = vm_name
    # in this case, tthis_path's only one vm.

    set_key(".env", "TF_VAR_subscription", str(subscription))
    set_key(".env", "TF_VAR_ressource_group_name", str(ressource_group))
    set_key(".env", "TF_VAR_vm_name", str(vm_name))
    set_key(".env", "TF_VAR_location", str(location))

    vm_info_cmd = [
        "az",
        "vm",
        "show",
        "--resource-group",
        ressource_group,
        "--name",
        vm_name,
    ]
    vm_info = subprocess.run(
        vm_info_cmd,
        capture_output=True,
        text=True,
    )
    vm_info_json = json.loads(vm_info.stdout)

    print("\n" * 5)
    size = vm_info_json.get("hardwareProfile", {}).get("vmSize", "")
    data["size"] = size
    name = vm_info_json.get("name", vm_name)
    data["name"] = name
    set_key(".env", "TF_VAR_size", str(size))

    adminUsername = vm_info_json.get("osProfile", {}).get("adminUsername", "")
    data["admin_username"] = adminUsername

    set_key(".env", "TF_VAR_name", str(name))
    set_key(".env", "TF_VAR_admin_username", str(adminUsername))

    storage_prof = vm_info_json.get("storageProfile", {})
    os_disk = storage_prof.get("osDisk", {})
    caching = os_disk.get("caching", "")
    data["caching"] = caching

    str_acc_type = os_disk.get("managedDisk", {}).get(
        "storageAccountType", ""
    )
    data["storage_account_type"] = str_acc_type

    img_ref = storage_prof.get("imageReference", {})
    publisher = img_ref.get("publisher", "")
    data["publisher"] = publisher

    sku = img_ref.get("sku", "")
    data["sku"] = sku

    version = img_ref.get("version", "")
    data["version"] = version

    offer = img_ref.get("offer", "")
    data["offer"] = offer
    set_key(".env", "TF_VAR_offer", str(offer))

    # if there are mulriple ids, modify this:
    network_interfaces = vm_info_json.get("networkProfile", {}).get(
        "networkInterfaces", []
    )
    network_id = network_interfaces[0]["id"] if network_interfaces else ""
    data["network_interface_id"] = network_id
    set_key(".env", "TF_VAR_network_interface_id", str(network_id))

    set_key(".env", "TF_VAR_caching", str(caching))
    set_key(".env", "TF_VAR_storage_account_type", str(str_acc_type))

    set_key(".env", "TF_VAR_publisher", str(publisher))
    set_key(".env", "TF_VAR_sku", str(sku))
    set_key(".env", "TF_VAR_image_version", str(version))

    load_dotenv()

    tailscale_apikey = os.getenv("tailscale_api")
    set_key(".env", "TF_VAR_tailscale_api_key", tailscale_apikey)
    passw = os.getenv("admin_password") or ""
    set_key(".env", "TF_VAR_admin_password", str(passw))

    print("\n" * 5)

    try:
        for k, v in dotenv_values(".env").items():
            if v is not None:
                os.environ[k] = str(v)
    except Exception as e:
        return f"Error: {e} ."

    time.sleep(5)
    this_path = os.path.dirname(os.path.abspath(__file__))
    try:
        final1 = subprocess.run(
            ["terraform", "init"],
            cwd=this_path,
            check=True,
            env=os.environ,
        )
        final2 = subprocess.run(
            ["terraform", "plan", "-input=false"],
            cwd=this_path,
            check=True,
            env=os.environ,
        )
        final3 = subprocess.run(
    ["terraform", "apply"],
    cwd=this_path,
    check=True,
    env=os.environ,
)

    except Exception as e:
        return f"Error: {e}"

    print("Variables set in the background succesffuly. ANd: terraform initiated & planned sucesfully")
    return data


if __name__ == "__main__":
    print(json.dumps(get_data(), indent=2))