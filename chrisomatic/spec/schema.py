from strictyaml import Str, Map, Regex, Optional, Seq, EmptyList, Bool, NullNone

api_url = Regex(r"^https?:\/\/.+\/api\/v1\/$")

user = Map({"username": Str(), "password": Str(), Optional("email"): Str()})

pipeline = Map(
    {"src": Str(), Optional("owner"): Str(), Optional("locked", default=True): Bool()}
)

plugin_specific = Map(
    {
        Optional("url"): Regex(
            r"https?:\/\/.+/api\/v1\/plugins\/\d+\/"
        ),
        Optional("name"): Str(),
        Optional("version"): Regex(r"^[0-9.]+$"),
        Optional("dock_image"): Str(),
        Optional("public_repo"): Regex(r".+:\/\/.+"),
        Optional("compute_resource", default=[]): EmptyList()
        | Seq(Str()),
        Optional("owner"): Str(),
    }
)

plugins_list = Seq(Str() | plugin_specific)

schema = Map(
    {
        Optional("version", default="1.0"): Regex(r"^1\.0$"),
        "on": Map(
            {
                "cube_url": api_url,
                Optional(
                    "chris_store_url", default=None, drop_if_none=False
                ): NullNone()
                | api_url,
                "chris_superuser": user,
                Optional(
                    "public_store", default=["https://chrisstore.co/api/v1/"]
                ): EmptyList()
                | Seq(api_url),
            }
        ),
        Optional("chris_store", default=None, drop_if_none=False): NullNone()
        | Map(
            {
                "users": Seq(user),
                Optional("pipelines", default=[]): EmptyList() | Seq(Str() | pipeline),
            }
        ),
        "cube": Map(
            {
                Optional("users", default=[]): EmptyList() | Seq(user),
                Optional("pipelines", default=[]): EmptyList() | Seq(Str() | pipeline),
                "compute_resource": Seq(
                    Map(
                        {
                            "name": Str(),
                            Optional("url", default=None): Str(),
                            Optional("username", default=None): Str(),
                            Optional("password", default=None): Str(),
                            Optional("description", default=None): Str(),
                        }
                    )
                ),
                Optional("plugins", default=[]): EmptyList() | plugins_list,
            }
        ),
    }
)
