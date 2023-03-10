# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import collections
import logging
import os

# from odoo.exceptions import ValidationError
import pickle
from datetime import datetime

import unidecode

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)

try:
    import MySQLdb

    assert MySQLdb
except (ImportError, AssertionError):
    _logger.info(
        'MySQLdb not available. Please install "mysqlclient" python package.'
    )

# TODO update me with your backup version
BACKUP_PATH = "/accorderie_canada/Intranet"
FILE_PATH = f"{BACKUP_PATH}/document/doc"
SECRET_PASSWORD = ""
DEBUG_LIMIT = False
LIMIT = 200
FORCE_ADD_USER_EMAIL = ""
GENERIC_EMAIL = f"%s_membre@accorderie.ca"
ENABLE_TIER_VALIDATION = True
DISABLE_CREATE_USER = False
MINIMUM_IMPORT = False


def post_init_hook(cr, e):
    _logger.info("Start migration of Accorderie of Quebec.")
    migration = MigrationAccorderie(cr)

    # General configuration
    migration.setup_configuration()

    # Create warehouse
    migration.set_head_quarter()

    # Create company
    migration.migrate_company()

    # Update user configuration
    migration.update_user(dry_run=False)

    # Create file
    if not MINIMUM_IMPORT:
        migration.migrate_muk_dms()

    # Create user
    migration.migrate_member()

    # Create fournisseur
    # migration.migrate_fournisseur()

    # Create demande service
    migration.migration_demande_service()

    # Create offre service
    migration.migration_offre_service()

    # Create hr timesheet
    # TODO à changer
    migration.migration_accorderie_echange_service()

    # Create product
    # migration.migrate_product()

    # Print email
    if migration.lst_generic_email:
        print("Got generic mail :")
        for mail in migration.lst_generic_email:
            print(f"\t{mail}")

    # Print warning
    if migration.lst_error:
        print("Got warning :")
        for warn in migration.lst_warning:
            print(f"\t{warn}")

    # Print error
    if migration.lst_error:
        print("Got error :")
        for err in migration.lst_error:
            print(f"\t{err}")


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class MigrationAccorderie:
    def __init__(self, cr):
        assert MySQLdb
        self.host = "localhost"
        self.user = "accorderie"
        self.passwd = "accorderie"
        self.db_name = "accorderie_log_2019"
        self.conn = MySQLdb.connect(
            host=self.host,
            user=self.user,
            passwd=self.passwd,
            db=self.db_name,
            charset="utf8",
            use_unicode=True,
        )
        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        self.cr = cr

        self.head_quarter = None

        self.dct_accorderie = {}
        self.dct_tbl_accorderie = {}
        self.dct_accorderie_accorderie = {}
        self.dct_accorderie_point_service = {}
        # self.dct_accorderie_by_email = {}
        self.dct_pointservice = {}
        self.dct_fichier = {}
        self.dct_produit = {}
        self.dct_membre = {}
        self.dct_accorderie_membre = {}
        self.dct_categorie_sous_categorie = {}
        self.dct_fournisseur = {}
        self.dct_demande_service = {}
        self.dct_offre_service = {}
        self.dct_echange_service = {}

        self.lst_generic_email = []
        self.lst_used_email = []

        self.lst_error = []
        self.lst_warning = []

        self.dct_tbl = self._fill_tbl()

    def set_head_quarter(self):
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            self.head_quarter = env["res.company"].browse(1)

    def _fill_tbl(self):
        """
        Fill all database in self.dct_tbl
        :return:
        """
        cur = self.conn.cursor()
        # Get all tables
        str_query = f"""SHOW tables;"""
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_ignore_table = [
            "tbl_log_acces",
            "tbl_commande_membre_produit",
            "tbl_fournisseur_produit_commande",
        ]

        dct_tbl = {a[0]: [] for a in tpl_result if "tbl" in a[0]}

        for table, lst_column in dct_tbl.items():
            if table in lst_ignore_table:
                msg = f"Skip table '{table}'"
                _logger.warning(msg)
                self.lst_warning.append(msg)
                continue

            _logger.info(f"Import in cache table '{table}'")
            str_query = f"""SHOW COLUMNS FROM {table};"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()
            lst_column_name = [a[0] for a in tpl_result]

            if not SECRET_PASSWORD:
                raise Exception(
                    "SECRET_PASSWORD is empty, fill it (search $password into"
                    " database of Accorderie)"
                )

            if table == "tbl_membre":
                str_query = f"""SELECT *,DECODE(MotDePasse,'{SECRET_PASSWORD}') AS MotDePasseRaw FROM tbl_membre;"""
                lst_column_name.append("MotDePasseRaw")
            else:
                str_query = f"""SELECT * FROM {table};"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()

            for lst_result in tpl_result:
                i = -1
                dct_value = {}
                for result in lst_result:
                    i += 1
                    # Exception fix database
                    if (
                        table == "tbl_membre"
                        and lst_column_name[i] == "Courriel"
                        and lst_result[0] == 927
                    ):
                        result = "mercier-hochelaga-maisonneuve@accorderie.ca"
                    dct_value[lst_column_name[i]] = result
                lst_column.append(Struct(**dct_value))

        return Struct(**dct_tbl)

    def setup_configuration(self, dry_run=False):
        _logger.info("Setup configuration")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            # CRM
            # team = env['crm.team'].browse(1)
            # Team name Europe need to be change in i18n french canadian
            # team.name = "Québec"

            # General configuration
            values = {
                # 'use_quotation_validity_days': True,
                # 'quotation_validity_days': 30,
                # 'portal_confirmation_sign': True,
                # 'portal_invoice_confirmation_sign': True,
                # 'group_sale_delivery_address': True,
                # 'group_sale_order_template': True,
                # 'default_sale_order_template_id': True,
                # 'use_sale_note': True,
                # 'sale_note': "N° TPS : \n"
                #              "N° TVQ : \n"
                #              "N° RBQ : 5775-6991-01\n"
                #              "N° BSP : SC 20047464\n"
                #              "Des frais de 2% par mois sont exigés sur tout solde impayé"
                #              " après la date d'échéance.",
                # 'refund_total_tip_amount_included_to_employee': True,
                # 'group_discount_per_so_line': True,
                # 'group_use_lead': True,
                # 'generate_lead_from_alias': True,
                # 'crm_alias_prefix': "service",
                "theme_color_brand": "#004a98",
                # 'theme_color_primary': "#2CD5C4",
                "theme_background_image": env.ref(
                    "accorderie_migrate_mysql.theme_background_image"
                ).datas,
                # 'branding_color_text': "#4c4c4c",
                # Enable multi company for each accorderie
                "group_multi_company": True,
                "company_share_partner": False,
                "company_share_product": False,
                # Ignore KPI digest
                "digest_emails": False,
                # Authentication
                "auth_signup_reset_password": True,
                # Commercial
                # TODO Cause bug when uninstall, need to do it manually
                # 'module_web_unsplash': False,
                # 'module_partner_autocomplete': False,
            }
            if not dry_run:
                event_config = env["res.config.settings"].sudo().create(values)
                event_config.execute()

    def update_user(self, dry_run=False):
        _logger.info("Update user preference")
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            administrator = env["res.users"].browse(2)
            # administrator.email = "admin@nuagelibre.ca"
            # Add all society to administrator
            administrator.company_ids = env["res.company"].search([]).ids

    def migrate_company(self, dry_run=False):
        _logger.info("Migrate company")
        # tbl_accorderie + tbl_pointservice

        head_quarter = None
        lst_child_company = []
        is_updated = False

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            if not self.dct_accorderie:
                is_updated = True
                # Accorderie
                i = 0
                for accorderie in self.dct_tbl.tbl_accorderie:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_accorderie)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    if accorderie.Nom == "Réseau Accorderie (du Qc)":
                        # Update main company
                        name = accorderie.Nom.strip()
                        head_quarter = env["res.company"].browse(1)
                        head_quarter.name = name
                        head_quarter.street = (
                            accorderie.AdresseAccorderie.strip()
                        )
                        head_quarter.zip = (
                            accorderie.CodePostalAccorderie.strip()
                        )
                        head_quarter.phone = accorderie.TelAccorderie.strip()
                        head_quarter.partner_id.fax = (
                            accorderie.TelecopieurAccorderie.strip()
                        )
                        head_quarter.email = (
                            accorderie.CourrielAccorderie.strip()
                        )
                        head_quarter.website = "www.accorderie.ca"
                        head_quarter.state_id = 543  # Quebec
                        head_quarter.country_id = 38  # Canada
                        head_quarter.tz = "America/Montreal"
                        head_quarter.create_date = (
                            accorderie.DateMAJ_Accorderie
                        )

                        # City
                        ville = self._get_ville(accorderie.NoVille)
                        head_quarter.city = ville.Ville

                        if accorderie.URL_LogoAccorderie:
                            data = open(
                                f"{self.logo_path}/{accorderie.URL_LogoAccorderie}",
                                "rb",
                            ).read()
                            head_quarter.logo = base64.b64encode(data)
                        else:
                            # obj.logo = base64.b64encode(env.ref("accorderie_migrate_mysql.logo_blanc_accorderie").datas),
                            _path = os.path.dirname(__file__)
                            data = open(
                                f"{_path}/static/img/logonoiblancaccorderie.jpg",
                                "rb",
                            ).read()
                            head_quarter.logo = base64.b64encode(data)
                        obj = head_quarter
                    else:
                        name = f"Accorderie {accorderie.Nom.strip()}"
                        ville = self._get_ville(accorderie.NoVille)
                        value = {
                            "name": name,
                            "city": ville.Ville,
                            "street": accorderie.AdresseAccorderie.strip(),
                            "zip": accorderie.CodePostalAccorderie.strip(),
                            "phone": accorderie.TelAccorderie.strip(),
                            "email": accorderie.CourrielAccorderie.strip(),
                            "state_id": 543,  # Quebec
                            "country_id": 38,  # Canada
                            "create_date": accorderie.DateMAJ_Accorderie,
                            "active": accorderie.NonVisible == 0,
                            "background_image": env.ref(
                                "accorderie_migrate_mysql.theme_background_image"
                            ).datas,
                            # 'website': result[14].strip(),
                        }

                        if accorderie.URL_LogoAccorderie:
                            data = open(
                                f"{self.logo_path}/{accorderie.URL_LogoAccorderie}",
                                "rb",
                            ).read()
                            value["logo"] = base64.b64encode(data)

                        obj = env["res.company"].create(value)
                        obj_acc = env["accorderie.accorderie"].create(
                            {
                                "company_id": obj.id,
                                # TODO implémenter region
                                # "region": accorderie.noregion,
                                # "ville": accorderie.noville,
                                # "arrondissement": accorderie.noarrondissement,
                                "create_date": accorderie.DateMAJ_Accorderie,
                                "message_grp_achat": accorderie.MessageGrpAchat,
                                "message_accueil": accorderie.MessageAccueil,
                                "url_public": accorderie.URL_Public_Accorderie,
                                "url_transactionnel": accorderie.URL_Transac_Accorderie,
                                "grp_achat_administrateur": accorderie.GrpAchat_Admin,
                                "grp_achat_membre": accorderie.GrpAchat_Accordeur,
                            }
                        )

                        comment_message = (
                            "<b>Note de migration</b><br/>Dernière mise à"
                            f" jour : {accorderie.DateMAJ_Accorderie}"
                        )

                        comment_value = {
                            "subject": (
                                "Note de migration - Plateforme Espace Membre"
                            ),
                            "body": f"<p>{comment_message}</p>",
                            "parent_id": False,
                            "message_type": "comment",
                            "author_id": SUPERUSER_ID,
                            "model": "accorderie.accorderie",
                            "res_id": obj_acc.id,
                        }
                        env["mail.message"].create(comment_value)

                        # try:
                        #     obj = env["res.company"].create(value)
                        #     obj_acc = env["accorderie.accorderie"].create(
                        #         {"company_id": obj.id}
                        #     )
                        # except Exception as e:
                        #     self.lst_error.append(e)
                        #     _logger.error(e)
                        #     continue
                        lst_child_company.append(obj)
                        obj.tz = "America/Montreal"
                        obj.partner_id.active = accorderie.NonVisible == 0
                        obj.partner_id.fax = (
                            accorderie.TelecopieurAccorderie.strip()
                        )
                        obj.partner_id.customer = False
                        obj.partner_id.supplier = False

                    self.dct_accorderie[accorderie.NoAccorderie] = obj
                    self.dct_tbl_accorderie[
                        accorderie.NoAccorderie
                    ] = accorderie
                    self.dct_accorderie_accorderie[
                        accorderie.NoAccorderie
                    ] = obj_acc
                    # self.dct_accorderie_by_email[obj.email] = obj
                    _logger.info(
                        f"{pos_id} - res.company - tbl_accorderie - ADDED"
                        f" '{name}' id {accorderie.NoAccorderie}"
                    )

                if head_quarter:
                    for child in lst_child_company:
                        child.parent_id = head_quarter.id

            # Point Service
            if not self.dct_pointservice:
                is_updated = True
                i = 0
                for pointservice in self.dct_tbl.tbl_pointservice:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_pointservice)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    tbl_membre = self._get_membre_point_service(
                        pointservice.NoPointService
                    )
                    tbl_accorderie = self.dct_tbl_accorderie[
                        pointservice.NoAccorderie
                    ]
                    name = (
                        "Point de service"
                        f" {pointservice.NomPointService.strip()}"
                    )
                    accorderie_obj = self.dct_accorderie.get(
                        pointservice.NoAccorderie
                    )

                    # TODO missing Telephone2 if exist, tpl_result[23]
                    value = {
                        "name": name,
                        "email": tbl_membre.Courriel.strip(),
                        "street": tbl_membre.Adresse.strip(),
                        "zip": tbl_membre.CodePostal.strip(),
                        "phone": tbl_membre.Telephone1,
                        "state_id": 543,  # Quebec
                        "country_id": 38,  # Canada
                        "create_date": pointservice.DateMAJ_PointService,
                        "parent_id": accorderie_obj.id,
                        "active": tbl_accorderie.NonVisible == 0,
                        "background_image": env.ref(
                            "accorderie_migrate_mysql.theme_background_image"
                        ).datas,
                        # 'website': result[14].strip(),
                    }

                    obj = env["res.company"].create(value)
                    accorderie_accorderie_obj = (
                        self.dct_accorderie_accorderie.get(
                            pointservice.NoAccorderie
                        )
                    )
                    obj_ps = env["accorderie.point.service"].create(
                        {
                            "company_id": obj.id,
                            "accorderie": accorderie_accorderie_obj.id,
                            "sequence": pointservice.OrdrePointService,
                            "create_date": pointservice.DateMAJ_PointService,
                        }
                    )

                    comment_message = (
                        "<b>Note de migration</b><br/>Dernière mise à"
                        f" jour : {pointservice.DateMAJ_PointService}"
                    )

                    comment_value = {
                        "subject": (
                            "Note de migration - Plateforme Espace Membre"
                        ),
                        "body": f"<p>{comment_message}</p>",
                        "parent_id": False,
                        "message_type": "comment",
                        "author_id": SUPERUSER_ID,
                        "model": "accorderie.point.service",
                        "res_id": obj_ps.id,
                    }
                    env["mail.message"].create(comment_value)

                    # try:
                    #     obj = env["res.company"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    obj.tz = "America/Montreal"
                    obj.partner_id.active = tbl_membre.MembreActif == -1
                    obj.partner_id.customer = False
                    obj.partner_id.supplier = False
                    # obj.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                    _logger.info(
                        f"{pos_id} - res.company - tbl_pointservice - "
                        f"ADDED '{name}' id {pointservice.NoPointService}"
                    )
                    # accorderie_email_obj = self.dct_accorderie_by_email.get(tbl_membre.Courriel.strip())
                    # name = f"Point de service {pointservice.NomPointService.strip()}"
                    # if not accorderie_email_obj:
                    #     accorderie_obj = self.dct_accorderie.get(pointservice.NoAccorderie)
                    #
                    #     # TODO missing Telephone2 if exist, tpl_result[23]
                    #     value = {
                    #         'name': name,
                    #         'email': tbl_membre.Courriel.strip(),
                    #         'street': tbl_membre.Adresse.strip(),
                    #         'zip': tbl_membre.CodePostal.strip(),
                    #         'phone': tbl_membre.Telephone1,
                    #         'state_id': 543,  # Quebec
                    #         'country_id': 38,  # Canada
                    #         'create_date': pointservice.DateMAJ_PointService,
                    #         'parent_id': accorderie_obj.id,
                    #         # 'website': result[14].strip(),
                    #     }
                    #
                    #     obj = env['res.company'].create(value)
                    #     obj.tz = "America/Montreal"
                    #     obj.partner_id.active = tbl_membre.MembreActif == -1
                    #     obj.partner_id.customer = False
                    #     obj.partner_id.supplier = False
                    #     # obj.partner_id.fax = accorderie.TelecopieurAccorderie.strip()
                    #     _logger.info(f"{pos_id} - res.company - tbl_pointservice - "
                    #           f"ADDED '{name}' id {pointservice.NoPointService}")
                    # else:
                    #     obj = accorderie_email_obj
                    #     _logger.info(f"{pos_id} - res.company - tbl_pointservice - "
                    #           f"DUPLICATED '{name}' id {pointservice.NoPointService} "
                    #           f"obj_id {obj.id}")
                    self.dct_pointservice[pointservice.NoPointService] = obj
                    self.dct_accorderie_point_service[
                        pointservice.NoPointService
                    ] = obj_ps

    def migrate_muk_dms(self):
        """
        Depend on company.
        :return:
        """
        _logger.info("Migrate files")
        # tbl_type_fichier and tbl_fichier

        if not self.dct_fichier:
            # Setup type fichier
            dct_type_fichier = {}
            with api.Environment.manage():
                env = api.Environment(self.cr, SUPERUSER_ID, {})

                i = 0
                for fichier in self.dct_tbl.tbl_type_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_type_fichier)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = fichier.TypeFichier
                    value = {
                        "name": name,
                        "create_date": fichier.DateMAJ_TypeFichier,
                    }

                    category_id = env["muk_dms.category"].create(value)
                    # try:
                    #     category_id = env["muk_dms.category"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    dct_type_fichier[fichier.Id_TypeFichier] = category_id
                    _logger.info(
                        f"{pos_id} - muk_dms.category - tbl_type_fichier -"
                        f" ADDED '{name}' id {fichier.Id_TypeFichier}"
                    )

                # Setup directory
                dct_storage = {}
                i = 0

                # for accorderie in list(self.dct_pointservice.values()) + list(self.dct_accorderie.values()):
                for accorderie in list(self.dct_accorderie.values()):
                    i += 1
                    pos_id = f"{i}/{len(self.dct_accorderie.values())}"
                    name = accorderie.name

                    value = {
                        "name": name,
                        "company": accorderie.id,
                    }

                    storage_id = env["muk_dms.storage"].create(value)
                    # try:
                    #     storage_id = env["muk_dms.storage"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue

                    if "/" in name:
                        name = name.replace("/", "_")
                    value = {
                        "name": name,
                        "root_storage": storage_id.id,
                        "is_root_directory": True,
                    }

                    directory_id = env["muk_dms.directory"].create(value)
                    # try:
                    #     directory_id = env["muk_dms.directory"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    if accorderie.id in dct_storage:
                        raise Exception(
                            f"Duplicate {accorderie} : {dct_storage}"
                        )

                    dct_storage[accorderie.id] = directory_id
                    _logger.info(
                        f"{pos_id} - muk_dms.storage - tbl_accorderie - ADDED"
                        f" '{name}' id {storage_id.id if storage_id else ''}"
                    )

                i = 0
                for fichier in self.dct_tbl.tbl_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_fichier)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = fichier.NomFichierOriginal

                    data = open(
                        f"{FILE_PATH}/{fichier.NomFichierStokage}", "rb"
                    ).read()
                    content = base64.b64encode(data)

                    # _, directory_id = self._get_storage(id_accorderie=result[2])

                    # type_fichier_id, _ = self._get_type_fichier(id_type_fichier=result[1])

                    category = dct_type_fichier.get(fichier.Id_TypeFichier).id

                    value = {
                        "name": name,
                        "category": category,
                        "active": fichier.Si_Disponible == 1,
                        "directory": dct_storage[
                            self.dct_accorderie.get(fichier.NoAccorderie).id
                        ].id,
                        "content": content,
                        "create_date": fichier.DateMAJ_Fichier,
                    }

                    try:
                        file_id = env["muk_dms.file"].create(value)
                    except Exception as e:
                        self.lst_error.append(e)
                        _logger.error(e)
                        continue
                    # Validate not duplicate
                    # files_id = env['muk_dms.file'].search([('name', '=', name), ('directory', '=', directory_id.id)])
                    # if not files_id:
                    #     file_id = env['muk_dms.file'].create(value)
                    # else:
                    #     if len(files_id) > 1:
                    #         raise Exception(f"ERROR, duplicate file id {i}")
                    #     if files_id[0].content == content:
                    #         _logger.info(f"{pos_id} - muk_dms.file - tbl_fichier - SKIPPED DUPLICATED SAME CONTENT '{name}' "
                    #               f"on storage '{directory_id.name}' id {fichier.Id_Fichier}")
                    #     else:
                    #         raise Exception(
                    #             f"ERROR, duplicate file id {i}, content is different, but same name '{name}'")

                    self.dct_fichier[fichier.Id_Fichier] = file_id
                    _logger.info(
                        f"{pos_id} - muk_dms.file - tbl_fichier - ADDED"
                        f" '{name}' on storage"
                        f" '{directory_id.name if directory_id else ''}' id"
                        f" {fichier.Id_Fichier}"
                    )

    def migrate_product(self):
        """
        :return:
        """
        _logger.info("Migrate products")
        # tbl_titre, tbl_produit

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_produit:
                dct_titre = {}

                product_cat_root_id = env["product.category"].create(
                    {"name": "Aliment"}
                )
                # try:
                #     product_cat_root_id = env["product.category"].create(
                #         {"name": "Aliment"}
                #     )
                # except Exception as e:
                #     self.lst_error.append(e)
                #     _logger.error(e)
                #     return

                i = 0
                for titre in self.dct_tbl.tbl_titre:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_titre)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = titre.Titre
                    value = {
                        "name": name,
                        "parent_id": product_cat_root_id.id,
                        "create_date": titre.DateMAJ_Titre,
                    }

                    product_cat_id = env["product.category"].create(value)
                    # try:
                    #     product_cat_id = env["product.category"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    dct_titre[titre.NoTitre] = product_cat_id
                    _logger.info(
                        f"{pos_id} - product.category - tbl_titre - ADDED"
                        f" '{name}' id {titre.NoTitre}"
                    )

                dct_produit = {}
                i = 0
                for produit in self.dct_tbl.tbl_produit:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_produit)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    titre_id = dct_titre.get(produit.NoTitre)
                    accorderie_obj = self.dct_accorderie.get(
                        produit.NoAccorderie
                    )
                    name = produit.NomProduit
                    active = produit.Visible_Produit == 1
                    value = {
                        "name": name,
                        "categ_id": titre_id.id,
                        "active": active,
                        "company_id": accorderie_obj.id,
                        "create_date": produit.DateMAJ_Produit,
                    }

                    product_id = env["product.template"].create(value)
                    # try:
                    #     product_id = env["product.template"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    dct_produit[produit.NoProduit] = product_id
                    _logger.info(
                        f"{pos_id} - product.template - tbl_produit - ADDED"
                        f" '{name}' id {produit.NoProduit} - is active"
                        f" {active}"
                    )

                self.dct_produit = dct_produit

    def migrate_member(self):
        """
        :return:
        """
        _logger.info("Migrate member")
        # tbl_membre

        # dct_debug_login = self._check_duplicate(
        #     self.dct_tbl.tbl_membre, "NomUtilisateur", verbose=False
        # )
        # dct_debug_email = self._check_duplicate(
        #     self.dct_tbl.tbl_membre, "Courriel", verbose=False
        # )
        # self.dct_tbl["tbl_membre|conflict"] = dct_debug
        # _logger.info("profile")
        # _logger.info(dct_debug_login)
        # _logger.info("email")
        # _logger.info(dct_debug_email)
        nb_membre_int = 0
        nb_membre_ext = 0
        nb_admin = 0

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_membre:
                dct_membre = {}
                dct_accorderie_membre = {}

                i = 0
                for membre in self.dct_tbl.tbl_membre:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_membre)}"

                    email = membre.Courriel.lower().strip()

                    if DEBUG_LIMIT and i > LIMIT:
                        # except for FORCE_ADD_USER_EMAIL
                        if FORCE_ADD_USER_EMAIL:
                            if FORCE_ADD_USER_EMAIL.lower() != email:
                                continue
                        else:
                            break

                    associate_point_service = None
                    if membre.EstUnPointService:
                        associate_point_service = self.dct_pointservice.get(
                            membre.NoPointService
                        ).partner_id

                    login = membre.NomUtilisateur
                    # Get the name in 1 field
                    if membre.Prenom and membre.Nom:
                        name = f"{membre.Prenom.strip()} {membre.Nom.strip()}"
                    elif membre.Prenom:
                        name = f"{membre.Prenom.strip()}"
                    elif membre.Nom:
                        name = f"{membre.Nom.strip()}"
                    else:
                        name = ""

                    if not associate_point_service and (not login or not name):
                        msg = (
                            f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                            f" EMPTY LOGIN '{name}' id {membre.NoMembre}"
                        )
                        _logger.warning(msg)
                        self.lst_warning.append(msg)
                        # lst_result .append((None, result))
                        continue

                    # Ignore test user
                    # if ("test" in name or "test" in login) and login not in [
                    #     "claudettestlaur"
                    # ]:
                    #     msg = (
                    #         f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                    #         f" TEST LOGIN name '{name}' login '{login}' id"
                    #         f" {membre.NoMembre}"
                    #     )
                    #     _logger.warning(msg)
                    #     self.lst_warning.append(msg)
                    #     continue

                    create_new_email = (
                        not email or email in self.lst_used_email
                    )

                    if create_new_email:
                        # Ignore duplicate login, create a new email
                        # if login in dct_debug_login.keys():
                        #     # TODO Need to merge it
                        #     msg = (
                        #         f"{pos_id} - res.partner - tbl_membre -"
                        #         f" SKIPPED DUPLICATED LOGIN name '{name}'"
                        #         f" login '{login}' email '{email}' id"
                        #         f" {membre.NoMembre}"
                        #     )
                        #     _logger.warning(msg)
                        #     self.lst_warning.append(msg)
                        #     continue
                        # Need an email for login, force create it
                        # email = GENERIC_EMAIL % i
                        email = unidecode.unidecode(
                            (GENERIC_EMAIL % login)
                            .lower()
                            .strip()
                            .replace(" ", "_")
                        )
                        nb_same_email = self.lst_generic_email.count(email)
                        if nb_same_email > 0:
                            email = unidecode.unidecode(
                                (
                                    GENERIC_EMAIL
                                    % f"{login}_{nb_same_email + 1}"
                                )
                                .lower()
                                .strip()
                                .replace(" ", "_")
                            )
                        self.lst_generic_email.append(email)
                        msg = f"Create generic email '{email}'"
                        _logger.warning(msg)
                        self.lst_warning.append(msg)
                    # elif email in dct_debug_email.keys():
                    #     # TODO merge user
                    #     msg = (
                    #         f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                    #         f" DUPLICATED EMAIL name '{name}' login '{login}'"
                    #         f" email '{email}' id {membre.NoMembre}"
                    #     )
                    #     _logger.warning(msg)
                    #     self.lst_warning.append(msg)
                    #     continue

                    if not associate_point_service:
                        self.lst_used_email.append(email)

                    # Show duplicate profile
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_login.items())[:15] for a in va[1] if a[37] == -1])
                    # Show duplicate email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1]])
                    # Show duplicate not empty email
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != ""])
                    # Show duplicate not empty email actif
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != "" and a[37] == -1])
                    # Show duplicate email active user
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1])
                    # duplicate email and duplicate user and active
                    # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1 and a[44] in dct_debug_login])

                    # Technique remplacé par l'utilisation du courriel
                    # if login in dct_debug_login.keys():
                    #     # Validate unique email
                    #     _logger.info(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED "
                    #           f"name '{name}' login '{login}' id {result[0]}")
                    #
                    #     if email in dct_debug_email:
                    #         _logger.info(dct_debug_email[email])
                    #     continue

                    company_id = self.dct_accorderie.get(membre.NoAccorderie)
                    accorderie_accorderie_id = (
                        self.dct_accorderie_accorderie.get(membre.NoAccorderie)
                    )
                    accorderie_point_service_id = (
                        self.dct_accorderie_point_service.get(
                            membre.NoPointService
                        )
                    )
                    accorderie_accorderie_transfer_de_id = (
                        self.dct_accorderie_accorderie.get(membre.TransfereDe)
                    )
                    city_name = self._get_ville(membre.NoVille)
                    if not associate_point_service:
                        value = {
                            "name": name,
                            "street": membre.Adresse.strip(),
                            "zip": membre.CodePostal.strip(),
                            "email": email,
                            "supplier": False,
                            "customer": True,
                            "state_id": 543,  # Quebec
                            "country_id": 38,  # Canada
                            "tz": "America/Montreal",
                            "active": membre.MembreActif
                            and "désinscrit" not in name,
                            "company_id": company_id.id,
                            # "create_date": membre.Date_MAJ_Membre,
                            "free_member": True,
                        }
                        # TODO add "create_date": membre.Date_MAJ_Membre, into mail message

                        if membre.Memo:
                            value["comment"] = membre.Memo.strip()

                        if city_name:
                            value["city"] = city_name.Ville

                        self._set_phone(membre, value)

                        obj_partner = env["res.partner"].create(value)
                    # try:
                    #     obj_partner = env["res.partner"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    if not associate_point_service:
                        permission = self._get_permission_no_membre(
                            membre.NoMembre
                        )

                        type_compte = self._get_type_compte_no_membre(
                            membre.NoMembre
                        )

                        is_admin = type_compte and (
                            type_compte.Admin
                            or type_compte.AdminChef
                            or type_compte.Reseau
                        )

                        is_internal_member = (
                            permission
                            and (
                                permission.GestionProfil
                                or permission.GestionCatSousCat
                                # not use
                                # or permission.GestionOffre
                                or permission.GestionOffreMembre
                                or permission.SaisieEchange
                                # not use
                                # or permission.Validation
                                or permission.GestionDmd
                                or permission.GroupeAchat
                                # not admin permission
                                or permission.ConsulterProfil
                                or permission.ConsulterEtatCompte
                                or permission.GestionFichier
                            )
                            or is_admin
                        )

                        if is_internal_member:
                            if is_admin:
                                nb_admin += 1
                            else:
                                nb_membre_int += 1
                        else:
                            nb_membre_ext += 1

                        groups_id = []
                        if is_internal_member:
                            groups_id.append(
                                (4, env.ref("base.group_user").id)
                            )
                            if is_admin:
                                if type_compte.Admin:
                                    groups_id.append(
                                        (
                                            4,
                                            env.ref(
                                                "accorderie.group_accorderie_admin"
                                            ).id,
                                        )
                                    )
                                if type_compte.AdminChef:
                                    groups_id.append(
                                        (
                                            4,
                                            env.ref(
                                                "accorderie.group_accorderie_admin_chef"
                                            ).id,
                                        )
                                    )
                                    groups_id.append(
                                        (
                                            4,
                                            env.ref(
                                                "base.group_erp_manager"
                                            ).id,
                                        )
                                    )
                                if type_compte.Reseau:
                                    groups_id.append(
                                        (
                                            4,
                                            env.ref(
                                                "accorderie.group_accorderie_admin_reseau"
                                            ).id,
                                        )
                                    )
                            if permission.GestionProfil:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_membre"
                                        ).id,
                                    )
                                )
                            if permission.GestionCatSousCat:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_type_service"
                                        ).id,
                                    )
                                )
                            if permission.GestionOffreMembre:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_offre_de_service"
                                        ).id,
                                    )
                                )
                            if permission.GestionDmd:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_demande_de_service"
                                        ).id,
                                    )
                                )
                            if permission.GroupeAchat:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_achat"
                                        ).id,
                                    )
                                )
                            if permission.GestionFichier:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_fichier"
                                        ).id,
                                    )
                                )
                            if permission.SaisieEchange:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_gestion_echange"
                                        ).id,
                                    )
                                )
                            if permission.ConsulterEtatCompte:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_consulter_etat_accorderie"
                                        ).id,
                                    )
                                )
                            if permission.ConsulterProfil:
                                groups_id.append(
                                    (
                                        4,
                                        env.ref(
                                            "accorderie.group_accorderie_consulter_membre"
                                        ).id,
                                    )
                                )

                        else:
                            groups_id.append(
                                (6, 0, [env.ref("base.group_portal").id])
                            )

                        if is_admin:
                            type_member = "admin"
                        elif is_internal_member:
                            type_member = "member interne"
                        else:
                            type_member = "member externe"

                        if not DISABLE_CREATE_USER:
                            no_reset_password = True
                            if not membre.MotDePasseRaw:
                                msg = (
                                    f"{pos_id} - MISSING PASSWORD, force"
                                    " recreate it - tbl_membre -"
                                    f" '{type_member}' - ADDED '{name}' login"
                                    f" '{login}' email '{email}' id"
                                    f" {membre.NoMembre}"
                                )
                                _logger.warning(msg)
                                self.lst_warning.append(msg)
                                no_reset_password = False
                            elif membre.MotDePasseRaw == membre.Courriel:
                                msg = (
                                    f"{pos_id} - PASSWORD same of email, force"
                                    " recreate it - tbl_membre -"
                                    f" '{type_member}' - ADDED '{name}' login"
                                    f" '{login}' email '{email}' id"
                                    f" {membre.NoMembre}"
                                )
                                _logger.warning(msg)
                                self.lst_warning.append(msg)
                                no_reset_password = False
                            elif membre.MotDePasseRaw == membre.NomUtilisateur:
                                msg = (
                                    f"{pos_id} - PASSWORD same of nom"
                                    " utilisateur, force recreate it -"
                                    f" tbl_membre - '{type_member}' - ADDED"
                                    f" '{name}' login '{login}' email"
                                    f" '{email}' id {membre.NoMembre}"
                                )
                                _logger.warning(msg)
                                self.lst_warning.append(msg)
                                no_reset_password = False
                            elif membre.MotDePasseRaw == membre.Nom:
                                msg = (
                                    f"{pos_id} - PASSWORD same of nom, force"
                                    " recreate it - tbl_membre -"
                                    f" '{type_member}' - ADDED '{name}' login"
                                    f" '{login}' email '{email}' id"
                                    f" {membre.NoMembre}"
                                )
                                _logger.warning(msg)
                                self.lst_warning.append(msg)
                                no_reset_password = False
                            elif membre.MotDePasseRaw == membre.Prenom:
                                msg = (
                                    f"{pos_id} - PASSWORD same of prenom,"
                                    " force recreate it - tbl_membre -"
                                    f" '{type_member}' - ADDED '{name}' login"
                                    f" '{login}' email '{email}' id"
                                    f" {membre.NoMembre}"
                                )
                                _logger.warning(msg)
                                self.lst_warning.append(msg)
                                no_reset_password = False

                            value = {
                                "name": name,
                                "active": membre.MembreActif == 0,
                                "login": email,
                                "password": membre.MotDePasseRaw,
                                "email": email,
                                "groups_id": groups_id,
                                "company_id": company_id.id,
                                "company_ids": [(4, company_id.id)],
                                "partner_id": obj_partner.id,
                            }

                            obj_user = (
                                env["res.users"]
                                .with_context(
                                    {"no_reset_password": no_reset_password}
                                )
                                .create(value)
                            )

                            dct_membre[membre.NoMembre] = obj_user

                        _logger.info(
                            f"{pos_id} - res.users - tbl_membre -"
                            f" '{type_member}' - ADDED '{name}' login"
                            f" '{login}' email '{email}' id {membre.NoMembre}"
                        )

                    # related: nom, active, adresse, codepostal, logo, telephone1, courriel
                    value_membre = {
                        "accorderie": accorderie_accorderie_id.id,
                        "point_service": accorderie_point_service_id.id,
                        # "type_communication": membre.NoTypeCommunication,
                        # "occupation": membre.NoOccupation,
                        # "origine": membre.NoOrigine,
                        # "situation_maison": membre.NoSituationMaison,
                        # "provenance": membre.NoProvenance,
                        # "revenu_familial": membre.NoRevenuFamilial,
                        # "arrondissement": membre.NoArrondissement,
                        # "ville": membre.NoVille,
                        # "region": membre.NoRegion,
                        "membre_ca": membre.MembreCA,
                        "part_social_paye": membre.PartSocialPaye,
                        "date_adhesion": membre.DateAdhesion,
                        # "adresse": membre.Adresse,
                        "telephone_1": membre.Telephone1,
                        "telephone_poste_1": membre.PosteTel1,
                        "telephone_2": membre.Telephone2,
                        "telephone_poste_2": membre.PosteTel2,
                        "telephone_3": membre.Telephone3,
                        "telephone_poste_3": membre.PosteTel3,
                        "achat_regrouper": membre.AchatRegrouper,
                        "pret_actif": membre.PretActif,
                        "bottin_tel": membre.BottinTel,
                        "bottin_courriel": membre.BottinCourriel,
                        "membre_conjoint": membre.MembreConjoint,
                        "membre_conjoint_id": membre.MembreConjoint,
                        # "memo": membre.Memo,
                        # "sexe": membre.Sexe,
                        "annee_naissance": membre.AnneeNaissance,
                        "nom_utilisateur": membre.NomUtilisateur,
                        "profil_approuver": membre.ProfilApprouver,
                        "membre_principal": membre.MembrePrinc,
                        "recevoir_courriel_groupe": membre.RecevoirCourrielGRP,
                        "pas_communication": membre.PasCommunication,
                        "description_membre": membre.DescriptionAccordeur,
                        "region": 1,
                        "ville": 1,
                        # "create_date": membre.Date_MAJ_Membre,
                    }
                    if membre.NoTypeTel1 and membre.NoTypeTel1 > 1:
                        value_membre["telephone_type_1"] = (
                            membre.NoTypeTel1 - 1
                        )
                    if membre.NoTypeTel2 and membre.NoTypeTel2 > 1:
                        value_membre["telephone_type_2"] = (
                            membre.NoTypeTel2 - 1
                        )
                    if membre.NoTypeTel3 and membre.NoTypeTel3 > 1:
                        value_membre["telephone_type_3"] = (
                            membre.NoTypeTel3 - 1
                        )

                    if associate_point_service:
                        value_membre["partner_id"] = associate_point_service.id
                    else:
                        value_membre["partner_id"] = obj_partner.id

                    if accorderie_accorderie_transfer_de_id:
                        value_membre[
                            "transfert_accorderie"
                        ] = accorderie_accorderie_transfer_de_id.id

                    obj_accorderie_membre = env["accorderie.membre"].create(
                        value_membre
                    )
                    point_service_info = (
                        " - POINT_SERVICE" if membre.EstUnPointService else ""
                    )
                    _logger.info(
                        f"{pos_id} - accorderie.membre - tbl_membre -"
                        f" '{type_member}'{point_service_info} - ADDED"
                        f" '{name}' login '{login}' email '{email}' id"
                        f" {obj_accorderie_membre.id}"
                    )
                    dct_accorderie_membre[
                        membre.NoMembre
                    ] = obj_accorderie_membre

                    # Add migration message
                    comment_message = (
                        "<b>Note de migration</b><br/>Dernière mise à"
                        f" jour : {membre.Date_MAJ_Membre}"
                    )

                    comment_value = {
                        "subject": (
                            "Note de migration - Plateforme Espace Membre"
                        ),
                        "body": f"<p>{comment_message}</p>",
                        "parent_id": False,
                        "message_type": "comment",
                        "author_id": SUPERUSER_ID,
                        "model": "accorderie.membre",
                        "res_id": obj_accorderie_membre.id,
                    }
                    env["mail.message"].create(comment_value)

                    # Add memo message
                    if membre.Memo:
                        html_memo = membre.Memo.replace("\n", "<br/>")
                        comment_message = (
                            f"<b>Mémo avant migration</b><br/>{html_memo}"
                        )

                        comment_value = {
                            "subject": (
                                "Mémo avant migration - Plateforme Espace"
                                " Membre"
                            ),
                            "body": f"<p>{comment_message}</p>",
                            "parent_id": False,
                            "message_type": "comment",
                            "author_id": SUPERUSER_ID,
                            "model": "accorderie.membre",
                            "res_id": obj_accorderie_membre.id,
                        }
                        env["mail.message"].create(comment_value)

                self.dct_membre = dct_membre
                self.dct_accorderie_membre = dct_accorderie_membre
                _logger.info(
                    f"Stat: {nb_admin} admin and {nb_membre_int} membre"
                    f" interne and {nb_membre_ext} membre externe."
                )

    def _get_permission_no_membre(self, no_membre):
        tpl_access = [
            a for a in self.dct_tbl.tbl_droits_admin if a.NoMembre == no_membre
        ]
        if tpl_access:
            return tpl_access[0]

    def _get_type_compte_no_membre(self, no_membre):
        tpl_access = [
            a for a in self.dct_tbl.tbl_type_compte if a.NoMembre == no_membre
        ]
        if tpl_access:
            return tpl_access[0]

    def migrate_fournisseur(self):
        """
        :return:
        """
        _logger.info("Migrate fournisseur")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_fournisseur:
                dct_fournisseur = {}

                i = 0
                for fournisseur in self.dct_tbl.tbl_fournisseur:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_fournisseur)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = fournisseur.NomFournisseur

                    accorderie_obj = self.dct_accorderie.get(
                        fournisseur.NoAccorderie
                    )
                    if "Accorderie" in name:
                        if not accorderie_obj.partner_id:
                            msg = (
                                "Missing partner associate to accorderie"
                                f" {name} fournisseur no"
                                f" {fournisseur.NoAccorderie}"
                            )
                            self.lst_error.append(msg)
                            _logger.error(msg)
                            continue
                        accorderie_obj.partner_id.supplier = True
                        new_comment = ""
                        if accorderie_obj.partner_id.comment:
                            new_comment = (
                                f"{accorderie_obj.partner_id.comment}\n"
                            )
                        accorderie_obj.partner_id.comment = (
                            f"{new_comment}Fournisseur : "
                            f"{fournisseur.NoteFournisseur.strip()}"
                        )
                        # accorderie_obj.create_date = fournisseur.DateMAJ_Fournisseur

                        dct_fournisseur[
                            fournisseur.NoFournisseur
                        ] = accorderie_obj.partner_id

                        _logger.info(
                            f"{pos_id} - res.partner - tbl_fournisseur -"
                            " UPDATED"
                            f" '{name}/{accorderie_obj.partner_id.name}' id"
                            f" {fournisseur.NoFournisseur}"
                        )
                        continue
                    # elif name in dct_debug.keys():
                    #     lst_duplicated = dct_debug.get(name)
                    #     _logger.info(f"{pos_id} - res.partner - tbl_fournisseur - SKIPPED '{name}' id {result[0]}")
                    #     continue

                    city_name = self._get_ville(fournisseur.NoVille)

                    value = {
                        "name": name,
                        "street": fournisseur.Adresse.strip(),
                        "zip": fournisseur.CodePostalFournisseur.strip(),
                        "phone": fournisseur.TelFournisseur.strip(),
                        "fax": fournisseur.FaxFounisseur.strip(),
                        "email": fournisseur.CourrielFournisseur.strip(),
                        "supplier": True,
                        "customer": False,
                        "state_id": 543,  # Quebec
                        "country_id": 38,  # Canada
                        "company_type": "company",
                        "comment": fournisseur.NoteFournisseur.strip(),
                        "tz": "America/Montreal",
                        "active": fournisseur.Visible_Fournisseur == 1,
                        "company_id": accorderie_obj.id,
                        "create_date": fournisseur.DateMAJ_Fournisseur,
                    }

                    if city_name:
                        value["city"] = city_name.Ville

                    obj = env["res.partner"].create(value)
                    # try:
                    #     obj = env["res.partner"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue

                    value_contact = {
                        "name": fournisseur.NomContact.strip(),
                        "function": fournisseur.PosteContact.strip(),
                        "email": fournisseur.CourrielContact.strip(),
                        "parent_id": obj.id,
                        "company_id": accorderie_obj.id,
                        "create_date": fournisseur.DateMAJ_Fournisseur,
                    }

                    obj_contact = env["res.partner"].create(value_contact)
                    # try:
                    #     obj_contact = env["res.partner"].create(value_contact)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue

                    dct_fournisseur[fournisseur.NoFournisseur] = obj
                    _logger.info(
                        f"{pos_id} - res.partner - tbl_fournisseur - ADDED"
                        f" '{name}' id {fournisseur.NoFournisseur}"
                    )

                self.dct_fournisseur = dct_fournisseur

    def migration_demande_service(self):
        """
        :return:
        """
        _logger.info("Migrate tbl_demande_service")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            if not self.dct_demande_service:
                dct_demande_service = {}

                i = 0
                for demande_service in self.dct_tbl.tbl_demande_service:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_demande_service)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = demande_service.TitreDemande

                    accorderie_obj = self.dct_accorderie_accorderie.get(
                        demande_service.NoAccorderie
                    )

                    membre_obj = self.dct_accorderie_membre.get(
                        demande_service.NoMembre
                    )

                    value = {
                        "titre": name,
                        "description": demande_service.Description,
                        "accorderie": accorderie_obj.id,
                        # "active": demande_service.Supprimer == 0,
                        # "approuver": demande_service.Approuve == -1,
                        "date_debut": demande_service.DateDebut,
                        "date_fin": demande_service.DateFin,
                    }
                    if (
                        not ENABLE_TIER_VALIDATION
                        and demande_service.Supprimer
                    ):
                        value["active"] = False

                    if membre_obj:
                        value["membre"] = membre_obj.id
                    else:
                        msg = (
                            f"{pos_id} - accorderie.demande.service -"
                            " tbl_demande_service - missing membre no"
                            f" '{demande_service.NoMembre}'"
                        )
                        _logger.warning(msg)
                        self.lst_warning.append(msg)

                    obj = env["accorderie.demande.service"].create(value)

                    dct_demande_service[demande_service.NoDemandeService] = obj
                    _logger.info(
                        f"{pos_id} - accorderie.demande.service -"
                        f" tbl_demande_service - ADDED '{name}' id"
                        f" {demande_service.NoDemandeService}"
                    )

                    if ENABLE_TIER_VALIDATION:
                        if not demande_service.Supprimer:
                            if demande_service.Approuve == -1:
                                # approuvé
                                val_tier_review = {
                                    "status": "approved",
                                    "model": "accorderie.demande.service",
                                    "res_id": obj.id,
                                    "definition_id": env.ref(
                                        "accorderie_approbation.accorderie_demande_service_tier_definition"
                                    ).id,
                                    "sequence": 1,
                                    "todo_by": "Migration bot",
                                    "done_by": SUPERUSER_ID,
                                    "requested_by": SUPERUSER_ID,
                                    "reviewed_date": datetime.now(),
                                    "comment": "Validé avant migration",
                                    "create_uid": SUPERUSER_ID,
                                    "write_uid": SUPERUSER_ID,
                                }
                                env["tier.review"].create(val_tier_review)
                            else:
                                # ask review
                                val_tier_review = {
                                    "status": "pending",
                                    "model": "accorderie.demande.service",
                                    "res_id": obj.id,
                                    "definition_id": env.ref(
                                        "accorderie_approbation.accorderie_demande_service_tier_definition"
                                    ).id,
                                    "sequence": 1,
                                    "todo_by": "Migration bot",
                                    "requested_by": SUPERUSER_ID,
                                    "comment": "Non validé avant migration",
                                    "create_uid": SUPERUSER_ID,
                                    "write_uid": SUPERUSER_ID,
                                }
                                env["tier.review"].create(val_tier_review)

                        if demande_service.Supprimer:
                            # Change active after review, or cause bug because review is ignore
                            obj.write({"active": False})

                self.dct_demande_service = dct_demande_service

    def migration_offre_service(self):
        """
        :return:
        """
        _logger.info("Migrate tbl_offre_service")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            if not self.dct_offre_service:
                dct_offre_service = {}

                i = 0
                for offre_service in self.dct_tbl.tbl_offre_service_membre:
                    i += 1
                    pos_id = (
                        f"{i}/{len(self.dct_tbl.tbl_offre_service_membre)}"
                    )

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    membre_obj = self.dct_accorderie_membre.get(
                        offre_service.NoMembre
                    )
                    accorderie_obj = self.dct_accorderie_accorderie.get(
                        offre_service.NoAccorderie
                    )
                    name = offre_service.TitreOffreSpecial

                    value = {
                        "titre": name,
                        "description": offre_service.Description,
                        "accorderie": accorderie_obj.id,
                        "accompli": offre_service.Fait,
                        "date_debut": offre_service.DateDebut,
                        "date_fin": offre_service.DateFin,
                        "create_date": offre_service.DateMAJ_ServiceMembre,
                        "condition": offre_service.ConditionOffre,
                        "date_affichage": offre_service.DateAffichage,
                        "disponibilite": offre_service.Disponibilite,
                        "approuve": offre_service.Approuve == -1,
                        "tarif": offre_service.Tarif,
                        "offre_special": offre_service.OffreSpecial,
                        "nb_consultation": offre_service.NbFoisConsulterOffreMembre,
                        # NoCategorieSousCategorie
                    }
                    if not ENABLE_TIER_VALIDATION:
                        value["active"] = not (
                            offre_service.Supprimer or offre_service.Fait
                        )

                    if membre_obj:
                        value["membre"] = membre_obj.id
                    else:
                        msg = (
                            f"{pos_id} - accorderie.offre.service -"
                            " tbl_offre_service_membre - missing membre no"
                            f" '{offre_service.NoMembre}'"
                        )
                        _logger.warning(msg)
                        self.lst_warning.append(msg)
                    # skill_id = self.dct_categorie_sous_categorie.get(
                    #     offre_service.NoCategorieSousCategorie
                    # )
                    # if skill_id:
                    #     value["skill_ids"] = [(6, 0, [skill_id.id])]
                    # else:
                    #     msg = (
                    #         "Missing categorie sous categorie id"
                    #         f" {offre_service.NoCategorieSousCategorie}"
                    #     )
                    #     self.lst_error.append(msg)
                    #     _logger.error(msg)

                    obj = env["accorderie.offre.service"].create(value)

                    dct_offre_service[offre_service.NoOffreServiceMembre] = obj
                    _logger.info(
                        f"{pos_id} - accorderie.offre.service -"
                        f" tbl_offre_service_membre - ADDED '{name}' id"
                        f" {offre_service.NoOffreServiceMembre}"
                    )

                    if ENABLE_TIER_VALIDATION:
                        if (
                            not offre_service.Fait
                            and not offre_service.Supprimer
                        ):
                            if offre_service.Approuve == -1:
                                # approuvé
                                val_tier_review = {
                                    "status": "approved",
                                    "model": "accorderie.offre.service",
                                    "res_id": obj.id,
                                    "definition_id": env.ref(
                                        "accorderie_approbation.accorderie_offre_service_tier_definition"
                                    ).id,
                                    "sequence": 1,
                                    "todo_by": "Migration bot",
                                    "done_by": SUPERUSER_ID,
                                    "requested_by": SUPERUSER_ID,
                                    "reviewed_date": datetime.now(),
                                    "comment": "Validé avant migration",
                                    "create_uid": SUPERUSER_ID,
                                    "write_uid": SUPERUSER_ID,
                                }
                                env["tier.review"].create(val_tier_review)
                            else:
                                # ask review
                                val_tier_review = {
                                    "status": "pending",
                                    "model": "accorderie.offre.service",
                                    "res_id": obj.id,
                                    "definition_id": env.ref(
                                        "accorderie_approbation.accorderie_offre_service_tier_definition"
                                    ).id,
                                    "sequence": 1,
                                    "todo_by": "Migration bot",
                                    "requested_by": SUPERUSER_ID,
                                    "comment": "Non validé avant migration",
                                    "create_uid": SUPERUSER_ID,
                                    "write_uid": SUPERUSER_ID,
                                }
                                env["tier.review"].create(val_tier_review)

                        if offre_service.Supprimer or offre_service.Fait:
                            # Change active after review, or cause bug because review is ignore
                            obj.write({"active": False})

                self.dct_offre_service = dct_offre_service

    def migration_accorderie_echange_service(self):
        """
        :return:
        """
        _logger.info("Migrate tbl_echange_service")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            if not self.dct_echange_service:
                dct_echange_service = {}

                # Create accorderie.echange.service
                i = 0
                for echange_service in self.dct_tbl.tbl_echange_service:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_echange_service)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    point_service_obj = self.dct_accorderie_point_service.get(
                        echange_service.NoPointService
                    )

                    lst_type_echange = list(
                        dict(
                            env["accorderie.echange.service"]
                            ._fields["type_echange"]
                            .selection
                        ).keys()
                    )
                    type_echange = lst_type_echange[
                        echange_service.TypeEchange - 1
                    ]

                    # NbHeure transform
                    # 15 000 = 15h
                    # 2 300 = 2h30
                    if not echange_service.NbHeure:
                        nb_heure = 0
                    else:
                        nb_heure = echange_service.NbHeure / 100
                        minute = str(int(nb_heure))[-2:]
                        minute = int(minute) if minute else 0
                        hour = str(int(nb_heure))[:-2]
                        hour = int(hour) if hour else 0
                        nb_heure = hour + minute / 60

                    value = {
                        "point_service": point_service_obj.id,
                        "nb_heure": nb_heure,
                        "date_echange": echange_service.DateEchange,
                        "type_echange": type_echange,
                        "remarque": echange_service.Remarque,
                        "commentaire": echange_service.Commentaire,
                        "transaction_valide": True,
                    }

                    if echange_service.NoMembreAcheteur:
                        membre_acheteur = self.dct_accorderie_membre.get(
                            echange_service.NoMembreAcheteur
                        )
                        if membre_acheteur:
                            value["membre_acheteur"] = membre_acheteur.id
                        else:
                            msg = (
                                "Le membre id"
                                f" '{echange_service.NoMembreAcheteur}' n'est"
                                " pas trouvable."
                            )
                            _logger.warning(msg)
                            self.lst_warning.append(msg)

                    if echange_service.NoMembreVendeur:
                        membre_vendeur = self.dct_accorderie_membre.get(
                            echange_service.NoMembreVendeur
                        )
                        if membre_vendeur:
                            value["membre_vendeur"] = membre_vendeur.id
                        else:
                            msg = (
                                "Le membre id"
                                f" '{echange_service.NoMembreVendeur}' n'est"
                                " pas trouvable."
                            )
                            _logger.warning(msg)
                            self.lst_warning.append(msg)

                    if echange_service.NoDemandeService:
                        demande_service = self.dct_demande_service.get(
                            echange_service.NoDemandeService
                        )
                        if demande_service:
                            value["demande_service"] = demande_service.id
                        else:
                            msg = (
                                "La demande de service id"
                                f" '{echange_service.NoDemandeService}' n'est"
                                " pas trouvable."
                            )
                            _logger.warning(msg)
                            self.lst_warning.append(msg)

                    if echange_service.NoOffreServiceMembre:
                        offre_service = self.dct_offre_service.get(
                            echange_service.NoOffreServiceMembre
                        )
                        if offre_service:
                            value["offre_service"] = offre_service.id
                        else:
                            msg = (
                                "L'offre de service id"
                                f" '{echange_service.NoOffreServiceMembre}'"
                                " n'est pas trouvable."
                            )
                            _logger.warning(msg)
                            self.lst_warning.append(msg)

                    obj = env["accorderie.echange.service"].create(value)

                    dct_echange_service[echange_service.NoEchangeService] = obj
                    _logger.info(
                        f"{pos_id} - accorderie.echange.service -"
                        " tbl_echange_service - ADDED id"
                        f" {echange_service.NoEchangeService}"
                    )

                self.dct_echange_service = dct_echange_service

    def _get_ville(self, no_ville: int):
        for ville in self.dct_tbl.tbl_ville:
            if ville.NoVille == no_ville:
                return ville

    def _get_membre(self, no_membre: int):
        for membre in self.dct_tbl.tbl_membre:
            if membre.NoMembre == no_membre:
                return membre

    def _get_membre_point_service(self, no_point_service: int):
        for membre in self.dct_tbl.tbl_membre:
            if (
                membre.NoPointService == no_point_service
                and membre.EstUnPointService
            ):
                return membre

    def _set_phone(self, membre, value):
        # Manage phone
        # result 22, 25, 28 is type
        # Type: 1 choose (empty)
        # Type: 2 domicile Phone
        # Type: 3 Travail À SUPPORTÉ
        # Type: 4 Cellulaire MOBILE
        # Type: 5 Téléavertisseur (pagette) NON SUPPORTÉ

        # Pagette
        if (
            membre.NoTypeTel1 == 5
            or membre.NoTypeTel2 == 5
            or membre.NoTypeTel3 == 5
        ):
            msg = (
                "Le pagette n'est pas supporté pour le membre"
                f" {membre.NoMembre}."
            )
            _logger.warning(msg)
            self.lst_warning.append(msg)

        # Travail
        if (
            membre.NoTypeTel1 == 3
            or membre.NoTypeTel2 == 3
            or membre.NoTypeTel3 == 3
        ):
            msg = (
                "Le téléphone travail n'est pas supporté pour le membre"
                f" {membre.NoMembre}."
            )
            _logger.warning(msg)
            self.lst_warning.append(msg)

        # MOBILE
        has_mobile = False
        if (
            membre.NoTypeTel1 == 4
            and membre.Telephone1
            and membre.Telephone1.strip()
        ):
            has_mobile = True
            value["mobile"] = membre.Telephone1.strip()
            if membre.PosteTel1 and membre.PosteTel1.strip():
                msg = (
                    "Le numéro de poste du mobile n'est pas supporté pour le"
                    f" membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
        if (
            membre.NoTypeTel2 == 4
            and membre.Telephone2
            and membre.Telephone2.strip()
        ):
            if has_mobile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_mobile = True
                value["mobile"] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    msg = (
                        "Le numéro de poste du mobile n'est pas supporté pour"
                        f" le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
        if (
            membre.NoTypeTel3 == 4
            and membre.Telephone3
            and membre.Telephone3.strip()
        ):
            if has_mobile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_mobile = True
                value["mobile"] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    msg = (
                        "Le numéro de poste du mobile n'est pas supporté pour"
                        f" le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)

        has_domicile = False
        if (
            membre.NoTypeTel1 == 2
            and membre.Telephone1
            and membre.Telephone1.strip()
        ):
            has_domicile = True
            value["phone"] = membre.Telephone1.strip()
            if (
                membre.PosteTel1
                and membre.PosteTel1
                and membre.PosteTel1.strip()
            ):
                msg = (
                    "Le numéro de poste du domicile n'est pas supporté pour"
                    f" le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
        if (
            membre.NoTypeTel2 == 2
            and membre.Telephone2
            and membre.Telephone2.strip()
        ):
            if has_domicile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_domicile = True
                value["phone"] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    msg = (
                        "Le numéro de poste du domicile n'est pas supporté"
                        f" pour le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
        if (
            membre.NoTypeTel3 == 2
            and membre.Telephone3
            and membre.Telephone3.strip()
        ):
            if has_domicile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_domicile = True
                value["phone"] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    msg = (
                        "Le numéro de poste du domicile n'est pas supporté"
                        f" pour le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)

    def _check_duplicate(self, tbl_membre, key, verbose=True):
        # Ignore duplicate since enable multi-company with different contact, not sharing
        # Debug duplicate data, need unique name
        dct_debug = collections.defaultdict(list)
        for result in tbl_membre:
            key_info = result.__dict__.get(key)
            if key_info is None:
                key_info = ""
            else:
                key_info = key_info.lower().strip()

            dct_debug[key_info].append(result)
        lst_to_remove = []
        for key_info, value in dct_debug.items():
            if len(value) > 1:
                if verbose:
                    _logger.warning(
                        f"Duplicate name ({len(value)})"
                        f" {key_info.lower().strip()}: {value}\n"
                    )
            else:
                lst_to_remove.append(key_info.lower().strip())
        for key_info in lst_to_remove:
            del dct_debug[key_info]
        return dct_debug
