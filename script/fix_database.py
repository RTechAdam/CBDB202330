#!/usr/bin/env python
import pymysql


# Fix date with string "0000-00-00"

# cr.execute("SET sql_mode = 'NO_ZERO_DATE';")
# cr.execute("SET sql_mode = 'NO_ZERO_IN_DATE';")

# query_search = """SELECT *
# FROM tbl_demande_service
# WHERE DateFin = "0000-00-00"
# """
#
# cr.execute(query_search)
# old_v = cr.fetchall()
#
# query = """UPDATE `tbl_demande_service`
# SET DateFin = NULL
# WHERE DateFin = "0000-00-00"
# """
#
# v = cr.execute(query)

# lst_echange_service = cr.fetchall()
# query_search = """SELECT *
# FROM tbl_echange_service
# """
#
# cr.execute(query_search)
# lst_echange_service = cr.fetchall()


def main():
    database = "accorderie_log_2019"
    host = "localhost"
    port = 3306
    user = "accorderie"
    password = "accorderie"
    schema = "public"

    conn = pymysql.connect(
        db=database, host=host, port=port, user=user, password=password
    )

    cr = conn.cursor()

    debug_over_generic(
        cr, "tbl_droits_admin", "NoMembre", "tbl_membre", "NoMembre"
    )
    debug_over_generic(
        cr, "tbl_type_compte", "NoMembre", "tbl_membre", "NoMembre"
    )
    debug_over_generic(
        cr,
        "tbl_categorie_sous_categorie",
        "NoCategorie",
        "tbl_categorie",
        "NoCategorie",
    )
    debug_over_generic(
        cr,
        "tbl_commande_membre_produit",
        "NoFournisseurProduitCommande",
        "tbl_fournisseur_produit_commande",
        "NoFournisseurProduitCommande",
    )
    debug_over_generic(
        cr, "tbl_echange_service", "NoMembreVendeur", "tbl_membre", "NoMembre"
    )
    debug_over_generic(
        cr,
        "tbl_fournisseur_produit",
        "NoFournisseur",
        "tbl_fournisseur",
        "NoFournisseur",
    )
    # TODO too much print ;-)
    # debug_over_generic(
    #     cr, "tbl_log_acces", "NoMembre", "tbl_membre", "NoMembre"
    # )
    debug_over_generic(
        cr,
        "tbl_membre",
        "NoOrigine",
        "tbl_origine",
        "NoOrigine",
    )

    delete_record(cr)
    alter_table(cr)
    replace_record(cr)
    add_foreign_key(cr)

    cr.close()


def debug_over_generic(cr, table1, field1, table2, field2):
    print(f"Debug over {table1} {field1}")
    query_search = f"""SELECT {field1}
    FROM {table1}
    """
    cr.execute(query_search)
    lst_1 = cr.fetchall()

    set_1 = set([a[0] for a in lst_1])

    query_search = f"""SELECT {field2}
    FROM {table2}
    """
    cr.execute(query_search)
    lst_2 = cr.fetchall()
    set_2 = set([a[0] for a in lst_2])

    set_missing = set_1.difference(set_2)
    # Result 7703
    if None in set_missing:
        set_missing.remove(None)
    print(set_missing)
    if set_missing:
        str_tpl = str(tuple(set_missing))
        if str_tpl.endswith(",)"):
            str_tpl = str_tpl.replace(",)", ")")
        query_search = f"""SELECT *
            FROM {table1}
            WHERE {field1} in {str_tpl}
            """
        cr.execute(query_search)
        lst_info = cr.fetchall()
        print(f"From table {table1}")
        print(lst_info)


def delete_record(cr):
    # Delete record
    print("Delete record")
    query_search = """DELETE FROM `tbl_droits_admin` WHERE NoMembre in (0, 945, 7703, 1253, 2655);"""
    cr.execute(query_search)
    query_search = """DELETE FROM `tbl_type_compte` WHERE NoMembre in (0, 945, 7703, 1253, 2652);"""
    cr.execute(query_search)
    query_search = """
    DELETE FROM `tbl_commande_membre_produit` 
    WHERE NoFournisseurProduitCommande in (22659, 22724, 22662, 22663, 22732, 22670, 22705, 22737, 22741, 22679, 22680, 22682, 22655);
    """
    cr.execute(query_search)
    query_search = """
    DELETE FROM `tbl_echange_service` 
    WHERE NoMembreVendeur in (7703);
    """
    cr.execute(query_search)
    query_search = """
    DELETE FROM `tbl_categorie_sous_categorie` 
    WHERE NoCategorie in (999);
    """
    cr.execute(query_search)


def alter_table(cr):
    # Fix tbl_echange_service NbHeure, transform time to float
    query_search = (
        """ALTER TABLE tbl_echange_service modify NbHeure float null;"""
    )
    cr.execute(query_search)
    query_search = """alter table tbl_commande_membre modify NoMembre int unsigned null;"""
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_arrondissement
    MODIFY NoVille int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_fournisseur_produit
    MODIFY NoFournisseur int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoTypeCommunication int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoOccupation int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoOrigine int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoSituationMaison int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoProvenance int unsigned null;
    """
    cr.execute(query_search)

    # Fix field for foreign key
    query_search = """
    ALTER TABLE tbl_membre
    MODIFY NoRevenuFamilial int unsigned null;
    """
    cr.execute(query_search)


def replace_record(cr):
    print("Replace existing record")
    # Replace 0 by null
    query_search = """UPDATE `tbl_accorderie` SET `NoArrondissement` = NULL WHERE NoArrondissement = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_commande_membre` SET `NoMembre` = NULL WHERE NoMembre = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_commentaire` SET `NoMembreViser` = NULL WHERE NoMembreViser = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_commentaire` SET `NoOffreServiceMembre` = NULL WHERE NoOffreServiceMembre = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_commentaire` SET `NoDemandeService` = NULL WHERE NoDemandeService = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_echange_service` SET `NoMembreVendeur` = NULL WHERE NoMembreVendeur = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_echange_service` SET `NoMembreAcheteur` = NULL WHERE NoMembreAcheteur = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_echange_service` SET `NoDemandeService` = NULL WHERE NoDemandeService = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_echange_service` SET `NoOffreServiceMembre` = NULL WHERE NoOffreServiceMembre = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_fournisseur_produit` SET `NoFournisseur` = NULL WHERE NoFournisseur = 0;"""
    cr.execute(query_search)
    query_search = (
        """UPDATE `tbl_log_acces` SET `NoMembre` = NULL WHERE NoMembre = 0;"""
    )
    cr.execute(query_search)
    query_search = (
        """UPDATE `tbl_membre` SET `NoCartier` = NULL WHERE NoCartier = 0;"""
    )
    cr.execute(query_search)
    query_search = (
        """UPDATE `tbl_membre` SET `NoCartier` = NULL WHERE NoCartier = 0;"""
    )
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoTypeCommunication` = NULL WHERE NoTypeCommunication = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoOccupation` = NULL WHERE NoOccupation = 0;"""
    cr.execute(query_search)
    query_search = (
        """UPDATE `tbl_membre` SET `NoOrigine` = NULL WHERE NoOrigine = 0;"""
    )
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoSituationMaison` = NULL WHERE NoSituationMaison = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoProvenance` = NULL WHERE NoProvenance = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoRevenuFamilial` = NULL WHERE NoRevenuFamilial = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_membre` SET `NoArrondissement` = NULL WHERE NoArrondissement = 0;"""
    cr.execute(query_search)
    query_search = """UPDATE `tbl_offre_service_membre` SET `NoCategorieSousCategorie` = NULL WHERE NoCategorieSousCategorie = 0;"""
    cr.execute(query_search)


def add_foreign_key(cr):
    print("Add foreign key")
    try:
        query_search = """
        ALTER TABLE tbl_accorderie
        DROP FOREIGN KEY foreign_key_tbl_accorderie_noarrondissement;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_accorderie
    ADD CONSTRAINT foreign_key_tbl_accorderie_noarrondissement
    FOREIGN KEY (NoArrondissement) REFERENCES tbl_arrondissement(NoArrondissement)
    on update set null on delete set null;
    """
    cr.execute(query_search)
    # - ville
    try:
        query_search = """
        ALTER TABLE tbl_accorderie
        DROP FOREIGN KEY foreign_key_tbl_accorderie_noville;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_accorderie
    ADD CONSTRAINT foreign_key_tbl_accorderie_noville
    FOREIGN KEY (NoVille) REFERENCES tbl_ville(NoVille);
    """
    cr.execute(query_search)
    # - region
    try:
        query_search = """
        ALTER TABLE tbl_accorderie
        DROP FOREIGN KEY foreign_key_tbl_accorderie_noregion;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_accorderie
    ADD CONSTRAINT foreign_key_tbl_accorderie_noregion
    FOREIGN KEY (NoRegion) REFERENCES tbl_region(NoRegion);
    """
    cr.execute(query_search)
    # - cartier
    try:
        query_search = """
        ALTER TABLE tbl_accorderie
        DROP FOREIGN KEY foreign_key_tbl_accorderie_nocartier;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_accorderie
    ADD CONSTRAINT foreign_key_tbl_accorderie_nocartier
    FOREIGN KEY (NoCartier) REFERENCES tbl_cartier(NoCartier);
    """
    cr.execute(query_search)

    # Arrondissement
    try:
        query_search = """
        ALTER TABLE tbl_arrondissement
        DROP FOREIGN KEY foreign_key_tbl_ville_noville;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_arrondissement
    ADD CONSTRAINT foreign_key_tbl_ville_noville
    FOREIGN KEY (NoVille) REFERENCES tbl_ville(NoVille)
    on update set null on delete set null;
    """
    cr.execute(query_search)

    # Cartier
    try:
        query_search = """
        ALTER TABLE tbl_cartier
        DROP FOREIGN KEY foreign_key_tbl_arrondissement_noarrondissement;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_cartier
    ADD CONSTRAINT foreign_key_tbl_arrondissement_noarrondissement
    FOREIGN KEY (NoArrondissement) REFERENCES tbl_arrondissement(NoArrondissement);
    """
    cr.execute(query_search)

    # Ville
    try:
        query_search = """
        ALTER TABLE tbl_ville
        DROP FOREIGN KEY foreign_key_tbl_region_noregion;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    ALTER TABLE tbl_ville
    ADD CONSTRAINT foreign_key_tbl_region_noregion
    FOREIGN KEY (NoRegion) REFERENCES tbl_region(NoRegion)
    on update set null on delete set null;
    """
    cr.execute(query_search)

    # achat_ponctuel
    try:
        query_search = """
        ALTER TABLE tbl_achat_ponctuel
        DROP FOREIGN KEY tbl_achat_ponctuel_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_achat_ponctuel
        add constraint tbl_achat_ponctuel_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # achat_ponctuel_produit
    # - achat_ponctuel
    try:
        query_search = """
        ALTER TABLE tbl_achat_ponctuel_produit
        DROP FOREIGN KEY tbl_achat_ponctuel_produit_tbl_achat_ponctuel_NoAchatPonctuel_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_achat_ponctuel_produit
        add constraint tbl_achat_ponctuel_produit_tbl_achat_ponctuel_NoAchatPonctuel_fk
            foreign key (NoAchatPonctuel) references tbl_achat_ponctuel (NoAchatPonctuel);
    """
    cr.execute(query_search)

    # - fournisseur_produit
    try:
        query_search = """
        ALTER TABLE tbl_achat_ponctuel_produit
        DROP FOREIGN KEY tbl_achat_pp_tbl_fournisseur_produit_NoFournisseurProduit_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_achat_ponctuel_produit
        add constraint tbl_achat_pp_tbl_fournisseur_produit_NoFournisseurProduit_fk
            foreign key (NoFournisseurProduit) references tbl_fournisseur_produit (NoFournisseurProduit);
    """
    cr.execute(query_search)

    # categorie_sous_categorie
    # - categorie
    try:
        query_search = """
        ALTER TABLE tbl_categorie_sous_categorie
        DROP FOREIGN KEY tbl_categorie_sous_categorie_tbl_categorie_NoCategorie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_categorie_sous_categorie
        add constraint tbl_categorie_sous_categorie_tbl_categorie_NoCategorie_fk
            foreign key (NoCategorie) references tbl_categorie (NoCategorie);
    """
    cr.execute(query_search)

    # - sous_categorie
    try:
        query_search = """
        ALTER TABLE tbl_categorie_sous_categorie
        DROP FOREIGN KEY tbl_csc_tbl_sous_categorie_NoSousCategorie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_categorie_sous_categorie
        add constraint tbl_csc_tbl_sous_categorie_NoSousCategorie_fk
            foreign key (NoSousCategorie) references tbl_sous_categorie (NoSousCategorie);
    """
    cr.execute(query_search)

    # tbl_commande
    try:
        query_search = """
        ALTER TABLE tbl_commande
        DROP FOREIGN KEY tbl_commande_tbl_pointservice_NoPointService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commande
        add constraint tbl_commande_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
    """
    cr.execute(query_search)

    # tbl_commande_membre
    # - commande
    try:
        query_search = """
        ALTER TABLE tbl_commande_membre
        DROP FOREIGN KEY tbl_commande_membre_tbl_commande_NoCommande_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commande_membre
        add constraint tbl_commande_membre_tbl_commande_NoCommande_fk
            foreign key (NoCommande) references tbl_commande (NoCommande);
    """
    cr.execute(query_search)

    # - membre
    try:
        query_search = """
        ALTER TABLE tbl_commande_membre
        DROP FOREIGN KEY tbl_commande_membre_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commande_membre
        add constraint tbl_commande_membre_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # tbl_fournisseur_produit_commande
    # - commande
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit_commande
        DROP FOREIGN KEY tbl_fournisseur_produit_commande_tbl_commande_NoCommande_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit_commande
        add constraint tbl_fournisseur_produit_commande_tbl_commande_NoCommande_fk
            foreign key (NoCommande) references tbl_commande (NoCommande);
    """
    cr.execute(query_search)

    # - fournisseur produit
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit_commande
        DROP FOREIGN KEY tbl_fpc_tbl_fournisseur_produit_NoFournisseurProduit_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit_commande
        add constraint tbl_fpc_tbl_fournisseur_produit_NoFournisseurProduit_fk
            foreign key (NoFournisseurProduit) references tbl_fournisseur_produit (NoFournisseurProduit);
    """
    cr.execute(query_search)

    # tbl_commande_membre_produit
    # - commande membre
    try:
        query_search = """
        ALTER TABLE tbl_commande_membre_produit
        DROP FOREIGN KEY tbl_cmp_tbl_commande_membre_NoCommandeMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commande_membre_produit
        add constraint tbl_cmp_tbl_commande_membre_NoCommandeMembre_fk
            foreign key (NoCommandeMembre) references tbl_commande_membre (NoCommandeMembre);
    """
    cr.execute(query_search)

    # - fournisseur produit commande
    try:
        query_search = """
        ALTER TABLE tbl_commande_membre_produit
        DROP FOREIGN KEY tbl_cmp_tbl_fpc_NoFournisseurProduitCommande_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commande_membre_produit
        add constraint tbl_cmp_tbl_fpc_NoFournisseurProduitCommande_fk
            foreign key (NoFournisseurProduitCommande) references tbl_fournisseur_produit_commande (NoFournisseurProduitCommande);
    """
    cr.execute(query_search)

    # tbl_commentaire
    # - point service
    try:
        query_search = """
        ALTER TABLE tbl_commentaire
        DROP FOREIGN KEY tbl_commentaire_tbl_pointservice_NoPointService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commentaire
        add constraint tbl_commentaire_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
    """
    cr.execute(query_search)

    # - membre source
    try:
        query_search = """
        ALTER TABLE tbl_commentaire
        DROP FOREIGN KEY tbl_commentaire_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commentaire
        add constraint tbl_commentaire_tbl_membre_NoMembre_fk
            foreign key (NoMembreSource) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # - membre visé
    try:
        query_search = """
        ALTER TABLE tbl_commentaire
        DROP FOREIGN KEY tbl_commentaire_tbl_membre_NoMembre_fk_2;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commentaire
        add constraint tbl_commentaire_tbl_membre_NoMembre_fk_2
            foreign key (NoMembreViser) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # - offre service membre
    try:
        query_search = """
        ALTER TABLE tbl_commentaire
        DROP FOREIGN KEY tbl_commentaire_tbl_offre_service_membre_NoOffreServiceMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commentaire
        add constraint tbl_commentaire_tbl_offre_service_membre_NoOffreServiceMembre_fk
            foreign key (NoOffreServiceMembre) references tbl_offre_service_membre (NoOffreServiceMembre);
    """
    cr.execute(query_search)

    # - demande service
    try:
        query_search = """
        ALTER TABLE tbl_commentaire
        DROP FOREIGN KEY tbl_commentaire_tbl_demande_service_NoDemandeService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_commentaire
        add constraint tbl_commentaire_tbl_demande_service_NoDemandeService_fk
            foreign key (NoDemandeService) references tbl_demande_service (NoDemandeService);
    """
    cr.execute(query_search)

    # tbl_demande_service
    # - membre
    try:
        query_search = """
        ALTER TABLE tbl_demande_service
        DROP FOREIGN KEY tbl_demande_service_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_demande_service
        add constraint tbl_demande_service_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # - accorderie
    try:
        query_search = """
        ALTER TABLE tbl_demande_service
        DROP FOREIGN KEY tbl_demande_service_tbl_accorderie_NoAccorderie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_demande_service
        add constraint tbl_demande_service_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
    """
    cr.execute(query_search)

    # tbl_dmd_adhesion
    # - accorderie
    try:
        query_search = """
        ALTER TABLE tbl_dmd_adhesion
        DROP FOREIGN KEY tbl_dmd_adhesion_tbl_accorderie_NoAccorderie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_dmd_adhesion
        add constraint tbl_dmd_adhesion_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
    """
    cr.execute(query_search)

    # tbl_droits_admin
    # - membre
    try:
        query_search = """
        ALTER TABLE tbl_droits_admin
        DROP FOREIGN KEY tbl_droits_admin_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_droits_admin
        add constraint tbl_droits_admin_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # tbl_echange_service
    # - point service
    try:
        query_search = """
        ALTER TABLE tbl_echange_service
        DROP FOREIGN KEY tbl_echange_service_tbl_pointservice_NoPointService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_echange_service
        add constraint tbl_echange_service_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
    """
    cr.execute(query_search)

    # - membre vendeur
    try:
        query_search = """
        ALTER TABLE tbl_echange_service
        DROP FOREIGN KEY tbl_echange_service_vendeur_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_echange_service
        add constraint tbl_echange_service_vendeur_tbl_membre_NoMembre_fk
            foreign key (NoMembreVendeur) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # - membre acheteur
    try:
        query_search = """
        ALTER TABLE tbl_echange_service
        DROP FOREIGN KEY tbl_echange_service_acheteur_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_echange_service
        add constraint tbl_echange_service_acheteur_tbl_membre_NoMembre_fk
            foreign key (NoMembreAcheteur) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # - demande service
    try:
        query_search = """
        ALTER TABLE tbl_echange_service
        DROP FOREIGN KEY tbl_echange_service_tbl_demande_service_NoDemandeService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_echange_service
        add constraint tbl_echange_service_tbl_demande_service_NoDemandeService_fk
            foreign key (NoDemandeService) references tbl_demande_service (NoDemandeService);
    """
    cr.execute(query_search)

    # - offre service membre
    try:
        query_search = """
        ALTER TABLE tbl_echange_service
        DROP FOREIGN KEY tbl_es_tbl_offre_service_membre_NoOffreServiceMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_echange_service
        add constraint tbl_es_tbl_offre_service_membre_NoOffreServiceMembre_fk
            foreign key (NoOffreServiceMembre) references tbl_offre_service_membre (NoOffreServiceMembre);
    """
    cr.execute(query_search)

    # tbl_fichier
    # - accorderie
    try:
        query_search = """
        ALTER TABLE tbl_fichier
        DROP FOREIGN KEY tbl_fichier_tbl_accorderie_NoAccorderie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fichier
        add constraint tbl_fichier_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
    """
    cr.execute(query_search)

    # - type fichier
    try:
        query_search = """
        ALTER TABLE tbl_fichier
        DROP FOREIGN KEY tbl_fichier_tbl_type_fichier_Id_TypeFichier_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fichier
        add constraint tbl_fichier_tbl_type_fichier_Id_TypeFichier_fk
            foreign key (Id_TypeFichier) references tbl_type_fichier (Id_TypeFichier);
    """
    cr.execute(query_search)

    # tbl_fournisseur
    # - accorderie
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur
        DROP FOREIGN KEY tbl_fournisseur_tbl_accorderie_NoAccorderie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur
        add constraint tbl_fournisseur_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
    """
    cr.execute(query_search)

    # - region
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur
        DROP FOREIGN KEY tbl_fournisseur_tbl_region_NoRegion_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur
        add constraint tbl_fournisseur_tbl_region_NoRegion_fk
            foreign key (NoRegion) references tbl_region (NoRegion);
    """
    cr.execute(query_search)

    # - ville
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur
        DROP FOREIGN KEY tbl_fournisseur_tbl_ville_NoVille_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur
        add constraint tbl_fournisseur_tbl_ville_NoVille_fk
            foreign key (NoVille) references tbl_ville (NoVille);
    """
    cr.execute(query_search)

    # tbl_fournisseur_produit
    # - fournisseur
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit
        DROP FOREIGN KEY tbl_fournisseur_produit_tbl_fournisseur_NoFournisseur_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit
        add constraint tbl_fournisseur_produit_tbl_fournisseur_NoFournisseur_fk
            foreign key (NoFournisseur) references tbl_fournisseur (NoFournisseur);
    """
    cr.execute(query_search)

    # - fournisseur_produit
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit
        DROP FOREIGN KEY tbl_fournisseur_produit_tbl_produit_NoProduit_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit
        add constraint tbl_fournisseur_produit_tbl_produit_NoProduit_fk
            foreign key (NoProduit) references tbl_produit (NoProduit);
    """
    cr.execute(query_search)

    # tbl_fournisseur_produit_point_service
    # - fournisseur_produit
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit_pointservice
        DROP FOREIGN KEY tbl_fpps_tbl_fournisseur_produit_NoFournisseurProduit_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit_pointservice
        add constraint tbl_fpps_tbl_fournisseur_produit_NoFournisseurProduit_fk
            foreign key (NoFournisseurProduit) references tbl_fournisseur_produit (NoFournisseurProduit);
    """
    cr.execute(query_search)

    # - point service
    try:
        query_search = """
        ALTER TABLE tbl_fournisseur_produit_pointservice
        DROP FOREIGN KEY tbl_fpps_tbl_pointservice_NoPointService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_fournisseur_produit_pointservice
        add constraint tbl_fpps_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
    """
    cr.execute(query_search)

    # tbl_log_access
    # - membre
    try:
        query_search = """
        ALTER TABLE tbl_log_acces
        DROP FOREIGN KEY tbl_log_acces_tbl_membre_NoMembre_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_log_acces
        add constraint tbl_log_acces_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
    """
    cr.execute(query_search)

    # tbl_membre
    # - cartier
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_cartier_NoCartier_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_cartier_NoCartier_fk
            foreign key (NoCartier) references tbl_cartier (NoCartier);
    """
    cr.execute(query_search)

    # - accorderie
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_accorderie_NoAccorderie_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
    """
    cr.execute(query_search)

    # - point service
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_pointservice_NoPointService_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
    """
    cr.execute(query_search)

    # - type communication
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_type_communication_NoTypeCommunication_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_type_communication_NoTypeCommunication_fk
            foreign key (NoTypeCommunication) references tbl_type_communication (NoTypeCommunication);
    """
    cr.execute(query_search)

    # - occupation
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_occupation_NoOccupation_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_occupation_NoOccupation_fk
            foreign key (NoOccupation) references tbl_occupation (NoOccupation);
    """
    cr.execute(query_search)

    # - origine
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_origine_NoOrigine_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_origine_NoOrigine_fk
            foreign key (NoOrigine) references tbl_origine (NoOrigine);
    """
    cr.execute(query_search)

    # - situation maison
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_situation_maison_NoSituationMaison_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_situation_maison_NoSituationMaison_fk
            foreign key (NoSituationMaison) references tbl_situation_maison (NoSituationMaison);
    """
    cr.execute(query_search)

    # - provenance
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_provenance_NoProvenance_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_provenance_NoProvenance_fk
            foreign key (NoProvenance) references tbl_provenance (NoProvenance);
    """
    cr.execute(query_search)

    # - revenu familial
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_revenu_familial_NoRevenuFamilial_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_revenu_familial_NoRevenuFamilial_fk
            foreign key (NoRevenuFamilial) references tbl_revenu_familial (NoRevenuFamilial);
    """
    cr.execute(query_search)

    # - arrondissement
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_arrondissement_NoArrondissement_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_arrondissement_NoArrondissement_fk
            foreign key (NoArrondissement) references tbl_arrondissement (NoArrondissement);
    """
    cr.execute(query_search)

    # - ville
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_ville_NoVille_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_ville_NoVille_fk
            foreign key (NoVille) references tbl_ville (NoVille);
    """
    cr.execute(query_search)

    # - region
    try:
        query_search = """
        ALTER TABLE tbl_membre
        DROP FOREIGN KEY tbl_membre_tbl_region_NoRegion_fk;
        """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_membre
        add constraint tbl_membre_tbl_region_NoRegion_fk
            foreign key (NoRegion) references tbl_region (NoRegion);
    """
    cr.execute(query_search)

    # tbl_mensualite
    # - pret
    try:
        query_search = """
            ALTER TABLE tbl_mensualite
            DROP FOREIGN KEY tbl_mensualite_tbl_pret_Id_Pret_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_mensualite
        add constraint tbl_mensualite_tbl_pret_Id_Pret_fk
            foreign key (Id_Pret) references tbl_pret (Id_Pret);
        """
    cr.execute(query_search)

    # tbl_offre_service_membre
    # - offre service membre
    try:
        query_search = """
            ALTER TABLE tbl_offre_service_membre
            DROP FOREIGN KEY tbl_offre_service_membre_tbl_membre_NoMembre_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_offre_service_membre
        add constraint tbl_offre_service_membre_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # - accorderie
    try:
        query_search = """
            ALTER TABLE tbl_offre_service_membre
            DROP FOREIGN KEY tbl_offre_service_membre_tbl_accorderie_NoAccorderie_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_offre_service_membre
        add constraint tbl_offre_service_membre_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
        """
    cr.execute(query_search)

    # - categorie sous categorie
    try:
        query_search = """
            ALTER TABLE tbl_offre_service_membre
            DROP FOREIGN KEY tbl_osm_tbl_categorie_sous_categorie_NoCategorieSousCategorie_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_offre_service_membre
        add constraint tbl_osm_tbl_categorie_sous_categorie_NoCategorieSousCategorie_fk
            foreign key (NoCategorieSousCategorie) references tbl_categorie_sous_categorie (NoCategorieSousCategorie);
        """
    cr.execute(query_search)

    # tbl_pointservice
    # - accorderie
    try:
        query_search = """
            ALTER TABLE tbl_pointservice
            DROP FOREIGN KEY tbl_pointservice_tbl_accorderie_NoAccorderie_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pointservice
        add constraint tbl_pointservice_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
        """
    cr.execute(query_search)

    # - membre
    try:
        query_search = """
            ALTER TABLE tbl_pointservice
            DROP FOREIGN KEY tbl_pointservice_tbl_membre_NoMembre_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pointservice
        add constraint tbl_pointservice_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # tbl_pointservice_fournisseur
    # - point service
    try:
        query_search = """
            ALTER TABLE tbl_pointservice_fournisseur
            DROP FOREIGN KEY tbl_pointservice_fournisseur_tbl_pointservice_NoPointService_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pointservice_fournisseur
        add constraint tbl_pointservice_fournisseur_tbl_pointservice_NoPointService_fk
            foreign key (NoPointService) references tbl_pointservice (NoPointService);
        """
    cr.execute(query_search)

    # - fournisseur
    try:
        query_search = """
            ALTER TABLE tbl_pointservice_fournisseur
            DROP FOREIGN KEY tbl_pointservice_fournisseur_tbl_fournisseur_NoFournisseur_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pointservice_fournisseur
        add constraint tbl_pointservice_fournisseur_tbl_fournisseur_NoFournisseur_fk
            foreign key (NoFournisseur) references tbl_fournisseur (NoFournisseur);
        """
    cr.execute(query_search)

    # tbl_pret
    # - membre
    try:
        query_search = """
            ALTER TABLE tbl_pret
            DROP FOREIGN KEY tbl_pret_tbl_membre_NoMembre_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pret
        add constraint tbl_pret_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # - membre intermediaire
    try:
        query_search = """
            ALTER TABLE tbl_pret
            DROP FOREIGN KEY tbl_pret_tbl_membre_NoMembre_fk_2;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pret
        add constraint tbl_pret_tbl_membre_NoMembre_fk_2
            foreign key (NoMembre_Intermediaire) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # - membre responsable
    try:
        query_search = """
            ALTER TABLE tbl_pret
            DROP FOREIGN KEY tbl_pret_tbl_membre_NoMembre_fk_3;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_pret
        add constraint tbl_pret_tbl_membre_NoMembre_fk_3
            foreign key (NoMembre_Responsable) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # tbl_produit
    # - titre
    try:
        query_search = """
            ALTER TABLE tbl_produit
            DROP FOREIGN KEY tbl_produit_tbl_titre_NoTitre_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_produit
        add constraint tbl_produit_tbl_titre_NoTitre_fk
            foreign key (NoTitre) references tbl_titre (NoTitre);
        """
    cr.execute(query_search)

    # - accorderie
    try:
        query_search = """
            ALTER TABLE tbl_produit
            DROP FOREIGN KEY tbl_produit_tbl_accorderie_NoAccorderie_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_produit
        add constraint tbl_produit_tbl_accorderie_NoAccorderie_fk
            foreign key (NoAccorderie) references tbl_accorderie (NoAccorderie);
        """
    cr.execute(query_search)

    # tbl_type_compte
    # - membre
    try:
        query_search = """
            ALTER TABLE tbl_type_compte
            DROP FOREIGN KEY tbl_type_compte_tbl_membre_NoMembre_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_type_compte
        add constraint tbl_type_compte_tbl_membre_NoMembre_fk
            foreign key (NoMembre) references tbl_membre (NoMembre);
        """
    cr.execute(query_search)

    # tbl_versement
    # - mensualité
    try:
        query_search = """
            ALTER TABLE tbl_versement
            DROP FOREIGN KEY tbl_versement_tbl_mensualite_Id_Mensualite_fk;
            """
        cr.execute(query_search)
    except Exception:
        pass

    query_search = """
    alter table tbl_versement
        add constraint tbl_versement_tbl_mensualite_Id_Mensualite_fk
            foreign key (Id_Mensualite) references tbl_mensualite (Id_Mensualite);
        """
    cr.execute(query_search)


if __name__ == "__main__":
    main()
