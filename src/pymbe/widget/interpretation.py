import ipywidgets as ipyw
import traitlets as trt

from .core import BaseWidget
from ..interpretation.interp_playbooks import random_generator_playbook
from ..graph.lpg import SysML2LabeledPropertyGraph


@ipyw.register
class Interpreter(ipyw.VBox, BaseWidget):

    STRATEGIES = {
        "random": random_generator_playbook,
    }

    description = trt.Unicode("Interpretation").tag(sync=True)
    instances: dict = trt.Dict()
    instances_box: ipyw.VBox = trt.Instance(ipyw.VBox, args=())
    lpg: SysML2LabeledPropertyGraph = trt.Instance(
        SysML2LabeledPropertyGraph,
        args=(),
    )
    update: ipyw.Button = trt.Instance(ipyw.Button)
    strategy_selector: ipyw.Dropdown = trt.Instance(ipyw.Dropdown)

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [self.instances_box]

    @trt.default("instances")
    def _make_instances(self):
        return random_generator_playbook(
            lpg=self.lpg,
            name_hints=dict(),
        )

    @trt.default("update")
    def _make_update_button(self):
        button = ipyw.Button(icon="update")
        button.on_click(self._update_instances)
        return button

    @trt.default("strategy_selector")
    def _make_strategy_selector(self):
        return ipyw.Dropdown(options=self.STRATEGIES)

    @trt.observe("lpg")
    def _on_lpg_update(self, change: trt.Bunch = None):
        change = change or trt.Bunch(new=None, old=None)

        old: SysML2LabeledPropertyGraph = change.old or None
        if isinstance(old, SysML2LabeledPropertyGraph):
            old.unobserve(self._update_instances)

        new: SysML2LabeledPropertyGraph = change.new or None
        if isinstance(new, SysML2LabeledPropertyGraph):
            new.observe(self._update_instances, "graph")

    @trt.observe("selected")
    def _on_updated_selected(self, *_):
        self.instances_box.children = [
            ipyw.Label(str(name))
            for element_id in self.selected
            for instances in self.instances[element_id]
            for name in instances
            if element_id in self.instances
        ]

    def _update_instances(self, *_):
        self.instances = self.strategy_selector.value(
            lpg=self.lpg,
            name_hints=dict(),
        )
