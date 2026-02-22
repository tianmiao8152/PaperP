from scapy.all import sniff, TCP, Raw
import re
import json
import regex
from ..utils import IO, t

class CaptureResult:
    def __init__(self):
        self.product_url = None
        self.request_body = None

def capture_ota_request(interface_ip="192.168.137.1"):
    IO.info(t("starting_capture") + f" ({interface_ip})")
    IO.info(t("waiting_packet"))

    result = CaptureResult()

    def process_packet(packet):
        if packet.haslayer(TCP) and packet.haslayer(Raw):
            try:
                # Try to decode payload
                payload = packet[Raw].load.decode(errors='ignore')
                
                # Check for OTA request pattern
                if "POST" in payload:
                    IO.debug(t("captured_post").format(payload[:100])) # Log first 100 chars
                
                if "POST /product/" in payload and "/ota/checkVersion" in payload:
                    IO.info(t("captured_request"))
                    # Regex to extract header line and JSON body
                    # Matches: POST ... HTTP/1.1 ... \r\n\r\n{...}
                    # We use a simpler approach: Split by double newline
                    parts = payload.split("\r\n\r\n", 1)
                    if len(parts) < 2:
                        return False
                        
                    header_part = parts[0]
                    body_part = parts[1]
                    
                    # Extract URL from POST line
                    url_match = re.search(r"POST (.*?) HTTP", header_part)
                    if url_match:
                        product_url = url_match.group(1)
                        IO.info(t("captured_request") + ": " + product_url)
                        
                        try:
                            # Use regex to find the first valid JSON object with recursive matching
                            # Pattern matches { ... } with support for nested braces
                            json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
                            match = json_pattern.search(body_part)
                            
                            if match:
                                json_str = match.group(0)
                                result.request_body = json.loads(json_str)
                                result.product_url = product_url
                                return True # Stop sniffing
                            else:
                                IO.warn(t("no_json_body"))
                        except json.JSONDecodeError:
                            IO.warn(t("json_parse_fail"))
                        except Exception as e:
                            IO.warn(t("json_extract_error").format(e))
            except Exception as e:
                pass
        return False

    # Start sniffing on TCP port 80
    # Note: 'store=0' prevents storing packets in memory
    sniff(filter="tcp port 80", prn=process_packet, stop_filter=process_packet, store=0)
    
    return result
