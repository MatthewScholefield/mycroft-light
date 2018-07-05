import re

from mycroft_core import MycroftSkill, Package, intent_handler
from subprocess import check_output


class IpSkill(MycroftSkill):
    @intent_handler('ip')
    def handle_ip(self, p: Package):
        ip_info = check_output(['ip', 'addr']).decode()
        all_ips = re.finditer(r'inet (([0-9]{1,3}\.?){4})\/[0-9]{1,2}.* ([a-z0-9]+)', ip_info)
        valid_ips = []
        other_ips = []
        for match in all_ips:
            ip, label = match.group(1, 3)
            if ip in ['127.0.0.1', '0.0.0.0']:
                continue
            if label[:3] in ['wlp', 'enp']:
                valid_ips.append(ip)
            else:
                other_ips.append(ip)

        ips = valid_ips or other_ips
        spoken_ips = [(' ' + self.locale('dot.txt')[0] + ' ').join(i.split('.')) for i in ips]
        if len(ips) > 1:
            p.data.update(ips=ips)
            p.data.update(spoken_ips=spoken_ips)
        elif len(ips) == 1:
            p.data.update(ip=ips[0])
            p.data.update(spoken_ip=spoken_ips[0])
