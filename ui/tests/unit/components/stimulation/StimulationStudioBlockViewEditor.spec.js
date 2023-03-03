import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioBlockViewEditor from "@/components/stimulation/StimulationStudioBlockViewEditor.vue";
import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

const test_protocolList = [
  { letter: "", color: "", label: "Create New" },
  {
    letter: "A",
    color: "#118075",
    label: "Tester",
    protocol: {
      name: "Tester",
      stimulationType: "V",
      restDuration: 20,
      timeUnit: "milliseconds",
      runUntilStopped: true,
      subprotocols: [
        {
          type: "Delay",
          duration: 15,
          unit: "seconds",
        },
        {
          type: "Delay",
          duration: 20,
          unit: "milliseconds",
        },
      ],
      detailedSubprotocols: [
        {
          type: "Delay",
          src: "/delay-tile.png",
          nested_protocols: [],
          repeat: { color: "d822f9", number_of_repeats: 0 },
          settings: {
            duration: 15,
            unit: "seconds",
          },
        },
      ],
    },
  },
];

describe("StimulationStudioDragAndDropPanel.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    store.state.stimulation.protocolList = JSON.parse(JSON.stringify(test_protocolList));
  });

  test("When mounting StimulationStudioDragAndDropPanel from the component file, Then default tab displayed should be basic, but can toggle with clicking each tab", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    expect(wrapper.vm.active_tab).toBe("Basic");
    await wrapper.find("#Advanced").trigger("click");
    expect(wrapper.vm.active_tab).toBe("Advanced");
    await wrapper.find("#Basic").trigger("click");
    expect(wrapper.vm.active_tab).toBe("Basic");
  });

  test("When a user wants to open a protocol settings to edit, Then the mutation will trigger saved settings to appear in the protocol editor", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const test_param_1 = store.state.stimulation.protocolList[1];
    const test_param_2 = {
      // for testing and building other fxns
      letter: "B",
      color: "#118075",
      label: "mock_tester",
      protocol: {
        name: "mock_tester",
        stimulationType: "C",
        runUntilStopped: false,
        restDuration: 40,
        timeUnit: "milliseconds",
        subprotocols: [],
        detailedSubprotocols: [],
      },
    };

    await store.dispatch("stimulation/editSelectedProtocol", test_param_1);
    expect(wrapper.vm.stimulationType_idx).toBe(1);
    expect(wrapper.vm.current_letter).toBe(test_param_1.letter);
    expect(wrapper.vm.restDuration).toBe("20");
    expect(wrapper.vm.stop_option_idx).toBe(0);
    expect(wrapper.vm.disabled_time).toBe(false);

    await store.dispatch("stimulation/editSelectedProtocol", test_param_2);
    expect(wrapper.vm.stimulationType_idx).toBe(0);
    expect(wrapper.vm.current_letter).toBe(test_param_2.letter);
    expect(wrapper.vm.restDuration).toBe("40");
    expect(wrapper.vm.stop_option_idx).toBe(1);
    expect(wrapper.vm.disabled_time).toBe(true);
  });

  test("When a user adds input to frequency input, Then the change will be recorded in data", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });

    await wrapper.find("#input-widget-field-protocol-rest").setValue("5");
    expect(wrapper.vm.restDuration).toBe("5");
  });

  test("When a user adds new protocol name, Then it will be checked if it is a unique name or if it already exists", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    await wrapper.vm.check_name_validity("test");
    expect(wrapper.vm.name_validity).toBe("border: 1px solid #19ac8a");
    expect(wrapper.vm.error_message).toBe("");

    await wrapper.vm.check_name_validity("");
    expect(wrapper.vm.name_validity).toBe("");
    expect(wrapper.vm.error_message).toBe("");

    await wrapper.vm.check_name_validity("Tester");
    expect(wrapper.vm.name_validity).toBe("border: 1px solid #bd3532");
    expect(wrapper.vm.error_message).toBe("*Protocol name already exists");
  });

  test("When a user selects from the stimulation type dropdown, Then the corresponding selection is stored", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    await wrapper.findAll("li").at(1).trigger("click");
    expect(store.state.stimulation.protocolEditor.stimulationType).toBe("C");
  });

  test("When a user imports a new protocol, Then the the next available protocol letter/color assignment will get updated", async () => {
    const updateSpy = jest.spyOn(StimulationStudioBlockViewEditor.methods, "update_protocols");
    mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const test_protocol = { label: "test", color: "#123456", letter: "B" };
    await store.commit("stimulation/setNewProtocol", test_protocol);
    expect(updateSpy).toHaveBeenCalledWith();
  });

  test("When exiting instance, Then instance is effectively destroyed", async () => {
    const destroyed_spy = jest.spyOn(StimulationStudioBlockViewEditor, "beforeDestroy");
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    wrapper.destroy();
    expect(destroyed_spy).toHaveBeenCalledWith();
  });

  test("When a user clicks the Clear All button, Then the dropdowns will reset to default value", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });

    await wrapper.setData({
      protocol_name: "test_name",
      restDuration: "10",
      name_validity: "border: 1px solid #19ac8a",
    });

    await store.commit("stimulation/resetState");

    expect(wrapper.vm.protocol_name).toBe("");
    expect(wrapper.vm.restDuration).toBe("");
    expect(wrapper.vm.name_validity).toBe("");
  });

  test("When 'Stimulate Until Complete' is selected, Then the input and time unit dropdown will be disabled", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const toggle_stop_options = wrapper.find("#small_dropdown_stop_options");
    const visible_option = wrapper.find("#stop_options_1");

    expect(wrapper.vm.disabled_time).toBe(false);

    await toggle_stop_options.trigger("click");
    await visible_option.trigger("click");

    expect(wrapper.vm.disabled_time).toBe(true);
  });

  // test("When a user clicks the trash icon and deletes the protocol, Then it should reset local data and mutate state", async () => {
  //   const wrapper = mount(StimulationStudioBlockViewEditor, {
  //     store,
  //     localVue,
  //   });
  //   await wrapper.find("#trash_icon").trigger("click");
  //   expect(wrapper.find("#del-protocol").isVisible()).toBe(true);
  //   await wrapper.vm.close_del_protocol_modal();
  //   expect(wrapper.find("#del-protocol").isVisible()).toBe(false);
  // });
});
