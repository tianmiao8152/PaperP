import hashlib
import re
import json
from ..utils import IO, t

class Patcher:
    @staticmethod
    def update_version_data(update_data, image_path, interface_ip):
        """
        Recalculate MD5 and SHA1 hashes for the patched firmware image.
        Updates the update_data dictionary with new hashes and local URL.
        
        Args:
            update_data: The JSON dictionary containing version info.
            image_path: Path to the patched firmware image.
            interface_ip: IP address of the local interface for the URL.
        """
        IO.info(t("calculating_hash"))
        
        version_data = update_data['data']['version']
        segment_md5_str = version_data['segmentMd5']
        
        # Handle segmentMd5 whether it's a string or object
        if isinstance(segment_md5_str, str):
            segment_md5 = json.loads(segment_md5_str)
        else:
            segment_md5 = segment_md5_str
            
        # Recalculate segment hashes
        for item in segment_md5:
            start = item['startpos']
            end = item['endpos']
            item['md5'] = Patcher.calc_segment_md5(image_path, start, end)
            
        # Update segmentMd5 in version_data
        if isinstance(segment_md5_str, str):
            version_data['segmentMd5'] = json.dumps(segment_md5)
        else:
            version_data['segmentMd5'] = segment_md5
            
        # Recalculate full file hashes
        version_data['md5sum'] = Patcher.calc_md5(image_path)
        version_data['sha'] = Patcher.calc_sha1(image_path)
        
        # Update URLs to point to local server
        local_url = f"http://{interface_ip}/image.img"
        version_data['deltaUrl'] = local_url
        version_data['bakUrl'] = local_url
        
        # Also update other potential URL fields
        if 'fullUrl' in version_data:
            version_data['fullUrl'] = local_url
            
        IO.debug(json.dumps(update_data, indent=2))
        return update_data

    @staticmethod
    def find_hash_patterns(filepath):
        IO.info(t("starting_password_search"))
        
        patterns = []
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                
            # Pattern 1: SHA256 (64 hex chars)
            # C++: buffer[i] == '#' && ... && buffer[i + 65] == ' ' && buffer[i + 66] == ' ' && buffer[i + 67] == '-'
            # i is '#'
            # i+1 to i+64 (64 chars) is hex
            # i+65 is ' '
            # i+66 is ' '
            # i+67 is '-'
            # Total length: 1 (#) + 64 (hash) + 2 (spaces) + 1 (-) = 68
            # Regex: b'#([0-9a-fA-F]{64})  -'
            # Capture group 1 is the hash.
            # Offset of hash is match.start(1)
            for match in re.finditer(rb'#([0-9a-fA-F]{64})  -', data):
                IO.info(t("hash_found_sha256").format(match.start(1)))
                patterns.append({'type': 'sha256', 'offset': match.start(1), 'length': 64})
                
            # Pattern 2: MD5 (32 hex chars)
            # C++: buffer[i] == '=' && buffer[i+1] == ' ' && buffer[i+2] == '"' && ... 
            # ... && buffer[i+35] == ' ' && buffer[i+36] == ' ' && buffer[i+37] == '-' && buffer[i+38] == '"'
            # i is '='
            # i+1 is ' '
            # i+2 is '"'
            # i+3 to i+34 (32 chars) is hex (hash)
            # i+35 is ' '
            # i+36 is ' '
            # i+37 is '-'
            # i+38 is '"'
            # Regex: b'= "([0-9a-fA-F]{32})  -"'
            # Capture group 1 is the hash.
            # Offset of hash is match.start(1)
            for match in re.finditer(rb'= "([0-9a-fA-F]{32})  -"', data):
                IO.info(t("hash_found_md5").format(match.start(1)))
                patterns.append({'type': 'md5', 'offset': match.start(1), 'length': 32})
                
        except Exception as e:
            IO.error(t("error_reading_file").format(e))
            
        return patterns

    @staticmethod
    def replace_hash(filepath):
        patterns = Patcher.find_hash_patterns(filepath)
        
        if not patterns:
            IO.error(t("no_passwords_found"))
            return False
            
        if len(patterns) > 1:
            IO.info(t("multiple_password_patterns"))

        pattern = patterns[0]
        
        new_password = ""
        while not new_password:
            new_password = IO.input(t("input_new_password")).strip()
            
        # Calculate new hash
        if pattern['type'] == 'md5':
            # Note: C++ adds a newline for MD5? "newPassword + '\n'"
            # Let's verify C++ code:
            # const std::string newHash = (positions[0].second == 32 ? HASH::MD5(newPassword + '\n') : HASH::SHA256(newPassword));
            new_hash = hashlib.md5((new_password + '\n').encode()).hexdigest()
        else:
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
        IO.info(f"New Hash: {new_hash}")
        
        try:
            with open(filepath, 'r+b') as f:
                f.seek(pattern['offset'])
                f.write(new_hash.encode())
                
            IO.info(t("patch_success"))
            return True
        except Exception as e:
            IO.error(f"Failed to patch file: {e}")
            return False

    @staticmethod
    def calc_md5(filepath):
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def calc_sha1(filepath):
        hash_sha1 = hashlib.sha1()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()

    @staticmethod
    def calc_segment_md5(filepath, start, end):
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            f.seek(start)
            remaining = end - start
            while remaining > 0:
                chunk_size = min(4096, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hash_md5.update(chunk)
                remaining -= len(chunk)
        return hash_md5.hexdigest()
