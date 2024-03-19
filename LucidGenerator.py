import requests
from drawio_network_plot import NetPlot

# Suppress warnings about unverified HTTPS requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def prompt_user_input():
    host = input("Enter the IP/hostname of your Dashboard instance: ")
    api_key = input("Enter your Dashboard API key: ")
    return host, api_key


def get_api_data(host, api_key, api_path):
    url = f'https://{host}/api/v0/{api_path}'
    headers = {'X-Auth-Token': api_key}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()


def main():
    host, api_key = prompt_user_input()

    # Gather data from the API
    devices_data = get_api_data(host, api_key, 'devices')
    links_data = get_api_data(host, api_key, 'resources/links')
    ports_data = get_api_data(host, api_key, 'ports?columns=ifName%2Cport_id%2CifAlias')

    # Transform API data into the format expected by drawio_network_plot
    devices = [
        {
            'nodeName': f"{device.get('hostname', '')}:{device.get('sysName', '')}".strip(':'),
            'nodeType': 'l3_switch',  # Temporary assumption
            'nodeDescription': 'NA'
        }
        for device in devices_data.get('devices', [])
    ]

    # Map port IDs to interface names
    port_to_interface = {str(port['port_id']): port['ifName'] for port in ports_data.get('ports', [])}

    device_id_to_name = {
        str(device['device_id']): f"{device.get('hostname', '')}:{device.get('sysName', '')}".strip(':')
        for device in devices_data.get('devices', [])
    }

    # Create links list for NetPlot, including port labels
    links = [
        {
            'sourceNodeID': device_id_to_name.get(str(link['local_device_id']), ''),
            'destinationNodeID': device_id_to_name.get(str(link['remote_device_id']), ''),
            'sourceLabel': port_to_interface.get(str(link['local_port_id']), ''),
            'destinationLabel': port_to_interface.get(str(link['remote_port_id']), '')
        }
        for link in links_data.get('links', [])
        if str(link['local_port_id']) in port_to_interface and str(link['remote_port_id']) in port_to_interface
    ]

    # Create the network plot
    net_plot = NetPlot()
    net_plot.addNodeList(devices)
    net_plot.addLinkList(links)

    drawio_xml = net_plot.display_xml()
    if isinstance(drawio_xml, bytes):
        drawio_xml = drawio_xml.decode('utf-8')

    with open('Network.xml', 'w', encoding='utf-8') as file:
        file.write(drawio_xml)

    print("Network  saved as 'network_diagram.drawio'.")


if __name__ == "__main__":
    main()


