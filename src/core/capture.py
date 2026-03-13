from scapy.all import sniff, TCP, Raw
import re
import json
import regex
from ..utils import IO, t

class CaptureResult:
    """抓包结果类，用于存储抓取到的OTA请求信息"""
    def __init__(self):
        """初始化CaptureResult对象"""
        self.product_url = None  # 产品URL
        self.request_body = None  # 请求体

def capture_ota_request(interface_ip="192.168.137.1"):
    """
    抓取OTA更新请求数据包
    
    参数:
        interface_ip (str): 网络接口IP地址，默认为"192.168.137.1"
    
    返回:
        CaptureResult: 包含产品URL和请求体的CaptureResult对象
    """
    IO.info(t("starting_capture") + f" ({interface_ip})")
    IO.info(t("waiting_packet"))

    result = CaptureResult()

    def process_packet(packet):
        """
        处理捕获到的数据包
        
        参数:
            packet: 捕获到的数据包
        
        返回:
            bool: 是否成功捕获到OTA请求
        """
        if packet.haslayer(TCP) and packet.haslayer(Raw):
            try:
                payload = packet[Raw].load.decode(errors='ignore')
                
                if "POST" in payload:
                    IO.debug(t("captured_post").format(payload[:100]))
                
                if "POST /product/" in payload and "/ota/checkVersion" in payload:
                    IO.info(t("captured_request"))
                    parts = payload.split("\r\n\r\n", 1)
                    if len(parts) < 2:
                        return False
                        
                    header_part = parts[0]
                    body_part = parts[1]
                    
                    url_match = re.search(r"POST (.*?) HTTP", header_part)
                    if url_match:
                        product_url = url_match.group(1)
                        IO.info(t("captured_request") + ": " + product_url)
                        
                        try:
                            json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
                            match = json_pattern.search(body_part)
                            
                            if match:
                                json_str = match.group(0)
                                result.request_body = json.loads(json_str)
                                result.product_url = product_url
                                return True
                            else:
                                IO.warn(t("no_json_body"))
                        except json.JSONDecodeError:
                            IO.warn(t("json_parse_fail"))
                        except Exception as e:
                            IO.warn(t("json_extract_error").format(e))
            except Exception as e:
                pass
        return False

    sniff(filter="tcp port 80", prn=process_packet, stop_filter=process_packet, store=0)
    
    return result
