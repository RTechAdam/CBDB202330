{
    "name": "Demo Accorderie",
    "version": "12.0.1.0",
    "author": "TechnoLibre",
    "license": "AGPL-3",
    "website": "https://technolibre.ca",
    "depends": ["accorderie_data"],
    "data": [
        "data/accorderie_accorderie.xml",
        "data/user_demo.xml",
        "data/accorderie_membre.xml",
        "data/accorderie_offre_service.xml",
        "data/accorderie_demande_service.xml",
        "data/accorderie_echange_service.xml",
        "data/accorderie_membre_favoris.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
