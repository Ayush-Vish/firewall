"""
DNS Query Logger with Process Mapping

This script captures DNS queries (UDP port 53) and maps them to running processes on the system.
It must be run with elevated permissions to access raw network sockets.

For Linux:
    Run with `sudo python3 domain_mapping.py` to ensure sufficient permissions.
"""

import threading
from scapy.all import sniff, DNS, DNSQR, UDP
import psutil
from datetime import datetime

# List to store the domain mapping objects with timestamps
app_domains = []

def get_domain_mapping():
    return app_domains

def capture_dns_requests(pkt):
    # Check if the packet contains DNS and is a query
    if pkt.haslayer(DNS) and pkt[DNS].qr == 0:  # qr=0 means it's a query, not a response
        domain = pkt[DNSQR].qname.decode()  # Extract the requested domain
        
        # Get the source port and the process associated with it
        if pkt.haslayer(UDP):  # Ensure the packet has a UDP layer
            src_port = pkt[UDP].sport  # Source port
            process_name = get_process_by_port(src_port)
            
            if process_name:
                # Get the current timestamp when the domain is accessed
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Check if the process is already in the app_domains list
                process_found = False
                for app in app_domains:
                    if app['process_name'] == process_name:
                        app['domains'].append({'domain': domain, 'timestamp': timestamp})  # Add the domain with timestamp
                        process_found = True
                        break
                
                # If the process is not found, add it to the list
                if not process_found:
                    app_domains.append({'process_name': process_name, 'domains': [{'domain': domain, 'timestamp': timestamp}]})

# Function to get the process name by port
def get_process_by_port(port):
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.pid:
            try:
                process = psutil.Process(conn.pid)
                return process.name()  # Return the process name
            except psutil.NoSuchProcess:
                pass
    return None  # Return None if no process is found for the port

# Start sniffing, filter for DNS packets (UDP port 53)
def start_dns_sniffing():
    sniff(filter="udp port 53", prn=capture_dns_requests, store=0)

# Function to start the sniffing in the background thread
def start_dns_in_background():
    dns_thread = threading.Thread(target=start_dns_sniffing, daemon=True)
    dns_thread.start()

# Example to run in the background
if __name__ == "__main__":
    print("Starting DNS sniffing...")
    start_dns_in_background()
    try:
        while True:
            # Keep the main program running to allow background sniffing
            time.sleep(5)
            print("Logged DNS queries:", get_domain_mapping())
    except KeyboardInterrupt:
        print("\nStopping DNS sniffing...")