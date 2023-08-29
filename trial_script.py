import netmiko
import argparse
import yaml
import getpass
import jinja2


def make_config_file(hostname: str, host_info: dict) -> str:
    """
    Render a configuration file template with the provided hostname and host_info.
    Process the configuration lines to remove empty lines and unnecessary whitespace.
    Write the processed configuration lines to a file with the hostname as the filename.
    Return the filename of the generated configuration file.
    """
    # Create a Jinja2 environment with the current directory as the template loader
    jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))

    # Load the template file named "template.j2" from the Jinja2 environment
    jinja_template = jinja_environment.get_template("template.j2")

    # Render the template with the provided hostname and host_info as variables
    raw_config_lines = jinja_template.render(HOSTNAME=hostname, HOST_DICT=host_info)
    proccessed_config_lines = []
    for line in raw_config_lines.split("\n"):
        if not line == "" and not line == "   " and not line == "  ":
            proccessed_config_lines.append(line)
    output_filename = f"{ hostname }.txt"
    with open(output_filename, "w") as output_file:
        for line in proccessed_config_lines:
            output_file.write(f"{ line }\n")

    # Return the filename of the generated configuration file
    return output_filename


def configure_device(
    host: str,
    mgmt_ip: str,
    config_file: str,
    password: str,
) -> bool:
    """
    Configures a network device using Netmiko library.

    Args:
        host (str): The hostname of the network device.
        mgmt_ip (str): The management IP address of the network device.
        config_file (str): The path to the configuration file
            containing the commands to be sent to the device.
        password (str): The password for authentication.

    Returns:
        bool: True if the configuration process is successful, False otherwise.
    """
    arista_vEOS = {
        "device_type": "arista_eos",
        "ip": mgmt_ip,
        "username": "admin",
        "password": password,
        "session_log": f"{ host }_netmiko_session.log",
    }
    try:
        with netmiko.ConnectHandler(**arista_vEOS) as net_connect:
            print(f"Connected to { host }")
            net_connect.enable()
            output = net_connect.send_config_from_file(config_file)
            output += net_connect.save_config()
            print(output)
    except Exception as e:
        print(e)
        return False
    return True


def main(yaml_input_file: str, admin_password: str) -> None:
    """
    Reads a YAML input file, generates configuration files for each device
    specified in the input, and configures the devices using Netmiko library.

    Args:
        yaml_input_file (str): The path to the YAML input file.
        admin_password (str): The password for authentication.

    Returns:
        None
    """
    try:
        with open(yaml_input_file, "r") as yaml_file:
            input_dictionary = yaml.safe_load(yaml_file)
    except Exception as error:
        print(error)
        print("please pass a valid yaml file")
        exit()
    config_files = {}
    for hostname, host_info in input_dictionary["devices"].items():
        config_files[hostname] = make_config_file(hostname, host_info)
    if input_dictionary["configure"]:
        for hostname, host_info in input_dictionary["devices"].items():
            if configure_device(
                host=hostname,
                mgmt_ip=host_info["management_ip"],
                config_file=config_files[hostname],
                password=admin_password,
            ):
                print(f"{ hostname } is configured")
            else:
                print(f"{ hostname } was not configured")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments using the argparse module in Python.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file", help="YAML file to import")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    password = getpass.getpass(
        "Enter the admin password for console servers and network devices: "
    )
    main(args.yaml_file, password)
