# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: distro
    author: Laurent Almeras
    version_added: "2.18"
    short_description: Resolve variable base on os_family / distribution / distribution_major_version
    description:
      - Lookup a value inside a dict with OS_FAMILY / DISTRIBUTION / DISTRIBUTION_VERSION keys
    options:
      _terms:
        description: Variable to lookup
        required: True
"""

EXAMPLES = """
    - name: resolve searching my_var['DISTRIBUTION_VERSION'], else my_var['DISTRIBUTION'] else my_var['OS_FAMILY']
      ansible.builtin.debug: msg="{{ lookup('distro', 'my_var')}}"
"""

RETURN = """
_raw:
  description:
    - correct dict key value from input variable, based on ansible facts distribution and os family.
  type: raw
"""

import itertools

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


DISTRIBUTION_SYNONYMS = [
    ['RedHat', 'CentOS'],
]


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        if len(terms) != 1:
            raise AnsibleError(f'Terms must be a unique value')

        ret = []
        for term in terms:
            if not isinstance(term, dict):
                raise AnsibleError(f'Terms must be a dict')
            ret.append(self._resolve(term, variables))
        if hasattr(self._templar, '_engine'):
            # ansible-core >= 2.19: templating is available
            return self._templar._engine.template(ret)
        else:
            # ansible-core < 2.19: templating is not available
            # templating should not be used by filter plugin
            # this should be enough
            return ret
        
    
    def _resolve(self, source_var, variables):
        ansible_distribution = variables.get('ansible_facts', {}).get('distribution', None)
        ansible_distributions = set([
            distro
                for distros in DISTRIBUTION_SYNONYMS
                    if ansible_distribution in distros
                for distro in distros
        ])
        ansible_distributions.add(ansible_distribution)
        ansible_distribution_version = variables.get('ansible_facts', {}).get('distribution_version', None)
        ansible_distribution_major_version = variables.get('ansible_facts', {}).get('distribution_major_version', None)
        ansible_os_family = variables.get('ansible_facts', {}).get('os_family', None)
        keys = []
        if ansible_distributions and ansible_distribution_version:
            keys.extend(['%s_%s' % (distribution, ansible_distribution_version)
                for distribution in ansible_distributions])
        if ansible_distributions and ansible_distribution_major_version:
            keys.extend(['%s_%s' % (distribution, ansible_distribution_major_version)
                for distribution in ansible_distributions])
        if ansible_distributions:
            keys.extend(['%s' % (distribution,)
                for distribution in ansible_distributions])
        if ansible_os_family:
            keys.extend(['%s' % (ansible_os_family,)])
        keys.append('default')
        ret = None
        
        for distro_string in keys:
            if distro_string in source_var:
                ret = source_var[distro_string]
                break

        return ret
