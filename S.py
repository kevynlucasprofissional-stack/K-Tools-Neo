from scapy.all import sniff, Ether, DHCP, BOOTP
import time


def decode_value(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def print_packet(packet):
    if not packet.haslayer(DHCP):
        return

    target_mac = None
    requested_ip = None
    hostname = None
    vendor_id = None

    if packet.haslayer(Ether):
        target_mac = packet[Ether].src

    if packet.haslayer(BOOTP):
        # Em alguns pacotes DHCP, o IP aparece aqui em vez de aparecer em requested_addr
        if packet[BOOTP].yiaddr != "0.0.0.0":
            requested_ip = packet[BOOTP].yiaddr

    dhcp_options = packet[DHCP].options

    for item in dhcp_options:
        if not isinstance(item, tuple):
            continue

        label, value = item

        if label == "requested_addr":
            requested_ip = value

        elif label == "hostname":
            hostname = decode_value(value)

        elif label == "vendor_class_id":
            vendor_id = decode_value(value)

    time_now = time.strftime("[%Y-%m-%d - %H:%M:%S]")

    print(
        f"{time_now} : "
        f"MAC={target_mac or 'desconhecido'} | "
        f"Hostname={hostname or 'não informado'} | "
        f"Vendor={vendor_id or 'não informado'} | "
        f"IP={requested_ip or 'não informado'}"
    )


def listen_dhcp():
    sniff(
        prn=print_packet,
        filter="udp and (port 67 or port 68)",
        store=False
    )


if __name__ == "__main__":
    listen_dhcp()