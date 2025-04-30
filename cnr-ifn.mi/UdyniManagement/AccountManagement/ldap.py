import os
import ldap
import ldap.modlist
import hashlib
import base64
import logging
import time

from django.conf import settings
from django.core.exceptions import PermissionDenied


class UdyniLdap(object):

    def __init__(self, username=None, password=None):
        # Connecto to LDAP
        try:
            # Initialize connection
            self._l = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)

            # Set connection options
            for k, v in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
                self._l.set_option(k, v)

            # If user and password are None bind as authbot
            if username is None or password is None:
                self._l.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
            else:
                user_dn = "uid={0:s},ou=People,dc=udyni,dc=lab".format(username)
                self._l.simple_bind_s(user_dn, password)

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "LDAP connection failed. Contact administrator.")

    def __process_ldap_exception(self, e, error):
        logger = logging.getLogger('django_auth_ldap')
        e_dict = e.args[0]
        msg_id = e_dict.get('msgid', -1)
        desc = e_dict.get('desc', 'Generic error')
        info = e_dict.get('info')
        msg = "Ldap error [{0!s}]: {1!s}".format(msg_id, desc)
        if info:
            msg += " (Additional information: {0!s})".format(info)
        logger.error(msg)
        raise PermissionDenied(error)

    @staticmethod
    def createSambaHash(password):
        """ Return the SMB MD4 hash for password
        """
        h = hashlib.new('md4', password.encode('utf-16le'))
        return h.hexdigest().upper().encode()

    @staticmethod
    def createLdapHash(password, salt=None):
        """ Retrun the SSHA1 hash for LDAP, encoded in base 64
        """
        if salt is None or len(salt) != 4:
            salt = os.urandom(4)
        hash = base64.b64encode(hashlib.new('sha1', password.encode() + salt).digest() + salt)
        return hash

    def checkPassword(self, username, password):
        """ Check that the given password match the given hash
        """
        user_dn = "uid={0:s},ou=People,dc=udyni,dc=lab".format(username)
        try:
            res = self._l.search_s(user_dn, ldap.SCOPE_SUBTREE,'(objectclass=person)', ['userPassword', ])
            hash = res[0][1]['userPassword'][0]
            if hash[0:6] == b"{SSHA}":
                hash = hash[6:]
            salt = base64.decodebytes(hash)[20:]
            new_hash = UdyniLdap.createLdapHash(password, salt)
            return hash == new_hash

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "LDAP password check failed. Contact administrator.")

    def changePassword(self, username, new_password):
        # Generate SAMBA password
        ldap_password = b'{SSHA}' + self.createLdapHash(new_password)
        nt_password = self.createSambaHash(new_password)
        lm_password = b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

        # User DN
        user_dn = "uid={0:s},ou=People,dc=udyni,dc=lab".format(username)

        try:
            # Update passwords and last set timestamps
            samba_last_change = int(time.time())
            shadow_last_change = int(samba_last_change / (24.0 * 3600.0))

            # Update SAMBA passwords
            modlist = [
                (ldap.MOD_REPLACE, "userPassword", ldap_password),
                (ldap.MOD_REPLACE, "sambaNTPassword", nt_password),
                (ldap.MOD_REPLACE, "sambaLMPassword", lm_password),
                (ldap.MOD_REPLACE, "sambaPwdLastSet", samba_last_change),
                (ldap.MOD_REPLACE, "shadowLastChange", shadow_last_change),
            ]
            self._l.modify_s(user_dn, modlist)

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "LDAP password change failed. Contact administrator.")

    def getUserAttribute(self, username, attribute):

        # User DN
        user_dn = "uid={0:s},ou=People,dc=udyni,dc=lab".format(username)

        try:
            res = self._l.search_s(user_dn, ldap.SCOPE_SUBTREE, '(objectclass=person)', [attribute, ])
            for r in res:
                if r[0] == user_dn:
                    return r[1].get(attribute)

        except ldap.NO_SUCH_OBJECT:
            return None

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to get attribute '{0:s}'".format(attribute))

    def getUserProfile(self, username):
        exclude_attrs = [
            'userPassword',
            'sambaNTPassword',
            'sambaLMPassword',
        ]

        # User DN
        user_dn = "uid={0:s},ou=People,dc=udyni,dc=lab".format(username)

        try:
            res = self._l.search_s(user_dn, ldap.SCOPE_SUBTREE, '(objectclass=person)')
            for r in res:
                if r[0] == user_dn:
                    # Filter results
                    for attr in exclude_attrs:
                        if attr in r[1]:
                            del r[1][attr]
                    return r[1]

        except ldap.NO_SUCH_OBJECT:
            return None

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to get user profile")

    def getNewUid(self):
        """ Retrun the next user UID
        """
        try:
            res = self._l.search_s('ou=People,dc=udyni,dc=lab', ldap.SCOPE_SUBTREE, attrlist=['uidNumber', ])
            uid = 10000
            for dn, entry in res:
                uids = entry.get('uidNumber')
                if uids is not None:
                    for u in uids:
                        n_uid = int(u)
                        if n_uid == 0:  # root
                            continue
                        if n_uid == 65534:  # nobody
                            continue
                        if n_uid >= uid:
                            uid = n_uid + 1
            return uid
        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to get user profile")

    def createUser(self, username, data):
        """ Create a new user
        Expect to find in data all the missing attributes. Mandatory ones are:
        - uidNumber
        - sn
        - givenName
        - mail
        - sambaNTPassword
        - userPassword
        """
        samba_last_change = time.time()
        shadow_last_change = int(samba_last_change / (24 * 3600))
        dn = f"uid={username},ou=People,dc=udyni,dc=lab"

        entry = {
            'objectClass': [
                b'top',
                b'person',
                b'organizationalPerson',
                b'posixAccount',
                b'shadowAccount',
                b'inetOrgPerson',
                b'sambaSamAccount',
                b'ldapPublicKey',
            ],
            'cn': username,
            'uid': username,
            'sambaLogonTime': 0,
            'sambaLogoffTime': 2147483647,
            'sambaKickoffTime': 2147483647,
            'sambaPwdCanChange': 0,
            'displayName': username,
            'sambaPrimaryGroupSID': 'S-1-5-21-1908601149-890380518-4032582813-513',
            'sambaLMPassword': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
            'sambaPwdMustChange': 1646492156,
            'sambaAcctFlags': '[XU]',
            'gecos': 'User',
            'gidNumber': 513,
            'sambaPwdLastSet': int(samba_last_change),
            'shadowLastChange': shadow_last_change,
        }

        entry.update(data)
        # Update samba SID
        entry['sambaSID'] = f"S-1-5-21-1908601149-890380518-4032582813-{entry['uidNumber']+1}"

        try:
            for k, v in entry.items():
                if type(v) is not list:
                    if type(v) is str:
                        entry[k] = [v.encode(), ]
                    else:
                        entry[k] = [str(v).encode(), ]
            modlist = ldap.modlist.addModlist(entry)
            self._l.add_s(dn, modlist)

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to create user profile")

    def deleteUser(self, username):
        dn = f"uid={username},ou=People,dc=udyni,dc=lab"
        try:
            self._l.delete_s(dn)
        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to delete user profile")

    def updateUser(self, username, attributes):
        dn = f"uid={username},ou=People,dc=udyni,dc=lab"
        try:
            res = self._l.search_s(dn, ldap.SCOPE_SUBTREE, '(objectclass=person)')
            profile = res[0][1]
            modlist = []
            for attr, value in attributes.items():
                if attr in profile:
                    if value == '' or value == b'':
                        modlist.append((ldap.MOD_DELETE, attr))
                    else:
                        if type(value) is bytes:
                            if value != profile[attr][0]:
                                modlist.append((ldap.MOD_REPLACE, attr, value))
                        else:
                             if value != profile[attr][0].decode():
                                modlist.append((ldap.MOD_REPLACE, attr, value.encode()))
                else:
                    if not (value == '' or value == b''):
                        modlist.append((ldap.MOD_ADD, attr, value if type(value) is bytes else value.encode()))

            self._l.modify_s(dn, modlist)

        except ldap.LDAPError as e:
            self.__process_ldap_exception(e, "Failed to create user profile")