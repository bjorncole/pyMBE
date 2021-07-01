from warnings import warn

import ipywidgets as ipyw
import traitlets as trt

from .core import BaseWidget
from ..interpretation.interp_playbooks import random_generator_playbook
from ..graph.lpg import SysML2LabeledPropertyGraph


@ipyw.register
class Interpreter(ipyw.VBox, BaseWidget):

    STRATEGIES = {
        "Random Generator": random_generator_playbook,
    }

    description: str = trt.Unicode("Interpretation").tag(sync=True)
    instances: dict = trt.Dict()
    instances_box: ipyw.VBox = trt.Instance(ipyw.VBox, args=())
    lpg: SysML2LabeledPropertyGraph = trt.Instance(
        SysML2LabeledPropertyGraph,
        args=(),
    )
    update_btn: ipyw.Button = trt.Instance(ipyw.Button)
    strategy_selector: ipyw.Dropdown = trt.Instance(ipyw.Dropdown)

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            ipyw.HBox(
                children=[self.strategy_selector, self.update_btn],
                layout=dict(overflow_y="hidden"),
            ),
            self.instances_box,
        ]

    @trt.default("instances")
    def _make_instances(self):
        instance_generator = self.STRATEGIES[self.strategy_selector.value]
        return instance_generator(lpg=self.lpg)

    @trt.default("update_btn")
    def _make_update_button(self):
        button = ipyw.Button(
            icon="retweet",
            layout=dict(height="40px", width="40px"),
            tooltip="Generate new instances",
        )
        button.on_click(self._update_instances)
        return button

    @trt.default("strategy_selector")
    def _make_strategy_selector(self):
        return ipyw.Dropdown(
            options=self.STRATEGIES,
            layout=dict(height="40px", width="auto"),
        )

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
        def make_element_label(element_id):
            name = self.lpg.elements_by_id.get(element_id, {}).get(
                "name",
                f"Unnamed Element: {element_id}",
            )
            return ipyw.HTML(
                value=f"""<h2>{name}</h2>"""
            )
        self.instances_box.children = [
            ipyw.VBox(
                [make_element_label(element_id)] +
                [
                    ipyw.VBox(
                        children=[
                            ipyw.HBox(
                                children=[
                                    ipyw.ToggleButton(
                                        description=f"{instance}",
                                        layout=ipyw.Layout(min_width="10%"),
                                    )
                                    for instance in instances
                                ],
                            )
                            for instances in self.instances[element_id]
                        ],
                        layout=ipyw.Layout(
                            flex_flow="wrap",
                            width="100%",
                        ),
                    ),
                ],
            )
            for element_id in self.selected
            if element_id in self.instances
        ]

    def _update_instances(self, *_):
        try:
            self.update_btn.disabled = True
            self.instances = self.strategy_selector.value(lpg=self.lpg)
            self._on_updated_selected()
        except Exception as exc:
            warn(f"Ran into an issue while updating instances: {exc}")
        finally:
            self.update_btn.disabled = False
