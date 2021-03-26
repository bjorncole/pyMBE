from dateutil import parser
from datetime import timezone

import requests
import sysml_v2_api_client as sysml2
import traitlets as trt

from .graph import SysML2LabeledPropertyGraph, SysML2RDFGraph


class SysML2Client(trt.HasTraits):
    """
        A traitleted SysML v2 API Client.

    ..todo:
        Make this capable of running independently.

    """

    host_url = trt.Unicode(
        default_value="http://sysml2-sst.intercax.com"
    )
    host_port = trt.Integer(
        default_value=9000,
        min=1,
        max=65535,
    )

    page_size = trt.Integer(
        default_value=2000,
        min=10,
    )

    _api_configuration: sysml2.Configuration = trt.Instance(sysml2.Configuration)
    _commits_api: sysml2.CommitApi = trt.Instance(sysml2.CommitApi)
    _elements_api: sysml2.ElementApi = trt.Instance(sysml2.ElementApi)
    _projects_api: sysml2.ProjectApi = trt.Instance(sysml2.ProjectApi)

    projects = trt.Dict()
    elements_by_id = trt.Dict()
    elements_by_type = trt.Dict()
    relationship_types = trt.Tuple()

    lpg: SysML2LabeledPropertyGraph = trt.Instance(SysML2LabeledPropertyGraph, args=tuple())
    rdf: SysML2RDFGraph = trt.Instance(SysML2RDFGraph, args=tuple())

    @trt.default("_api_configuration")
    def _make_api_configuration(self):
        return sysml2.Configuration(host=self.host)

    @trt.default("_commits_api")
    def _make_commits_api(self):
        with sysml2.ApiClient(self._api_configuration) as client:
            api = sysml2.CommitApi(client)
        return api

    @trt.default("_elements_api")
    def _make_elements_api(self):
        with sysml2.ApiClient(self._api_configuration) as client:
            api = sysml2.ElementApi(client)
        return api

    @trt.default("_projects_api")
    def _make_projects_api(self):
        with sysml2.ApiClient(self._api_configuration) as client:
            api = sysml2.ProjectApi(client)
        return api

    @trt.default("projects")
    def _make_projects(self):
        projects = self._projects_api.get_projects()
        return {
            project.id: dict(
                created=parser.parse(
                    " ".join(project.name.split()[-6:])
                ).astimezone(timezone.utc),
                full_name=project.name,
                name=" ".join(project.name.split()[:-6]),
            )
            for project in projects
        }

    @trt.observe("host_url", "host_port")
    def _update_api_configuration(self, *_):
        old_api_configuration = self._api_configuration
        self._api_configuration = self._make_api_configuration()
        if old_api_configuration:
            del old_api_configuration

    @trt.observe("_api_configuration")
    def _update_apis(self, *_):
        for api_type in ("commit", "element", "project"):
            api_attr = f"_{api_type}s_api"
            old_api = getattr(self, api_attr)
            api_maker = getattr(self, f"_make{api_attr}")
            setattr(self, api_attr, api_maker())
            del old_api
        self.project_selector.options = self._get_project_options()

    @property
    def host(self):
        return f"{self.host_url}:{self.host_port}"

    @property
    def elements_url(self):
        return (
            f"{self.host}/"
            f"projects/{self.selected_project_id}/"
            f"commits/{self.selected_commit_id}/"
            f"elements?page[size]={self.page_size}"
        )

    def by_id(self, id_: str):
        return self.elements_by_id[id_]

    def name_by_id(self, id_: str):
        return self.by_id(id_).get("Name")
    
    def _get_elements_from_server(self):
        response = requests.get(self.elements_url)
        if not response.ok:
            raise requests.HTTPError(
                f"Failed to retrieve elements from '{self.elements_url}', "
                f"reason: {response.reason}"
            )
        return response.json()
    
    def _update_elements(self, *_, elements=None):
        elements = elements or []
        self.relationship_types = sorted({
            element["@type"]
            for element in elements
            if "relatedElement" in element
        })
        self.elements_by_id = {
            element["@id"]: element
            for element in elements
        }
        element_types = {element["@type"] for element in elements}
        self.elements_by_type = {
            element_type: tuple([
                element["@id"]
                for element in elements
                if element["@type"] == element_type
            ])
            for element_type in element_types
        }

    
    def _download_elements(self):
        elements = self._get_elements_from_server()
        self._update_elements(elements=elements)
        self.lpg.update(client=self)
        self.rdf.update(client=self)
