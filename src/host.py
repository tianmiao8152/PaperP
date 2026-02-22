import os
import shutil
import ctypes
from .utils import IO, t

class HostManager:
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    BACKUP_PATH = r"C:\Windows\System32\drivers\etc\hosts.paper_bak"
    TARGET_DOMAIN = "iotapi.abupdate.com"
    REDIRECT_IP = "0.0.0.0"
    
    @staticmethod
    def enable_redirect(ip="0.0.0.0"):
        try:
            # Backup hosts file
            if not os.path.exists(HostManager.BACKUP_PATH):
                IO.info(f"{t('hosts_backup_create')}: {HostManager.BACKUP_PATH}")
                shutil.copy2(HostManager.HOSTS_PATH, HostManager.BACKUP_PATH)
            
            content = ""
            encoding = 'utf-8'
            try:
                with open(HostManager.HOSTS_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                encoding = 'gbk' # Fallback to GBK
                try:
                    with open(HostManager.HOSTS_PATH, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    encoding = 'latin-1' # Last resort
                    with open(HostManager.HOSTS_PATH, 'r', encoding='latin-1') as f:
                        content = f.read()

            # Check if entry already exists
            entry = f"{ip} {HostManager.TARGET_DOMAIN}"
            if entry in content:
                return True
                
            # Append entry
            prefix = ""
            if content and not content.endswith('\n'):
                prefix = "\n"
                
            with open(HostManager.HOSTS_PATH, 'a', encoding=encoding) as f:
                f.write(f"{prefix}{entry}\n")
                
            IO.info(t("hosts_modified"))
            HostManager.flush_dns()
            return True
        except Exception as e:
            IO.error(t("hosts_modify_fail").format(e))
            return False

    @staticmethod
    def disable_redirect():
        try:
            if not os.path.exists(HostManager.BACKUP_PATH):
                return # Nothing to restore
                
            # Restore from backup
            IO.info(t('hosts_backup_restore'))
            shutil.copy2(HostManager.BACKUP_PATH, HostManager.HOSTS_PATH)
            os.remove(HostManager.BACKUP_PATH)
            
            IO.info(t("hosts_restored"))
            HostManager.flush_dns()
            return True
        except Exception as e:
            IO.error(t("hosts_restore_fail").format(e))
            return False

    @staticmethod
    def flush_dns():
        try:
            lib = ctypes.windll.dnsapi
            lib.DnsFlushResolverCache()
            IO.debug(t("dns_flushed"))
        except:
            IO.warn(t("dns_flush_fail"))
