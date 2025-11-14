{
    "name"          : "Execute Query",
    "version"       : "1.0",
    "author"        : "Miftahussalam-ITGRUPO",
    "website"       : "https://blog.miftahussalam.com",
    "category"      : "Extra Tools",
    "license"       : "LGPL-3",
    "support"       : "me@miftahussalam.com",
    "summary"       : "Execute query from database",
    "description"   : """
        Execute query without open postgres
Goto : Settings > Technical
    """,
    "depends"       : [
        "base",
        "mail",
    ],
    "data"          : [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/ms_query_view.xml",
        "wizard/login_sql_wizard.xml",
    ],
    "demo"          : [],
    "test"          : [],
    "images"        : [
        "static/description/images/main_screenshot.png",
        "static/description/images/main_1.png",
        "static/description/images/main_2.png",
        "static/description/images/main_3.png",
    ],
    "qweb"          : [],
    "css"           : [],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
}