#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 16:20:12 2022

@author: Michele Devetta
"""

import copy
import re


def menu_include(reference):
    mod_name, submod_name = reference.split('.')
    module = __import__(mod_name)
    submodule = getattr(module, submod_name)
    return submodule.menu


class UdyniMenu(object):

    def __check_permissions(self, user, permissions):
        if user.is_superuser:
            return True
        elif permissions is None:
            return True
        else:
            check = []
            for perm in permissions:
                mandatory = False
                if perm[0] == '!':
                    perm = perm[1:]
                    mandatory = True
                if not user.has_perm(perm):
                    if mandatory:
                        return False
                else:
                    check.append(True)
            return len(check) > 0

    def getMenu(self, user):
        """ Return a menu structure filtered by the given user permissions
        """
        out = []
        menu_structure = __import__('UdyniManagement').urls.menu
        for h in menu_structure:

            new_h = {'name': h['name'], 'sections': []}

            if len(h['sections']):
                # We have sections
                for s in h['sections']:
                    # Check permissions
                    ok = self.__check_permissions(user, s['permissions'])

                    if ok:
                        # Permissions ok, create new section in output
                        new_s = copy.deepcopy(s)
                        new_s['subsections'] = []
                        new_s['id'] = re.sub(r"\s+", "_", new_s['name'].lower())

                        # User has permisions, so we can proceed with subsections
                        if len(s['subsections']):
                            for ss in s['subsections']:
                                ok = self.__check_permissions(user, ss['permissions'])
                                if ok:
                                    new_s['subsections'].append(copy.deepcopy(ss))

                        new_h['sections'].append(new_s)

            if len(new_h['sections']):
                out.append(new_h)

        return out
