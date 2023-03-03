import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioProtocolViewer from "@/components/stimulation/StimulationStudioProtocolViewer.vue";
import StimulationStudioWaveform from "@/components/stimulation/StimulationStudioWaveform.vue";
import Vuex from "vuex";
import { convertXYArraysToD3Array } from "@/js_utils/waveform_data_formatter.js";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

const test_protocol_order = [
  {
    type: "Biphasic",
    src: "placeholder",
    color: "#ffff1",
    pulse_settings: {
      phaseOneDuration: 30,
      phaseOneCharge: 20,
      interphaseInterval: 5,
      phaseTwoDuration: 10,
      phaseTwoCharge: -5,
      postphaseInterval: 10,
      total_active_duration: {
        duration: 2000,
        unit: "milliseconds",
      },
      num_cycles: 2,
    },
  },
  {
    type: "Monophasic",
    src: "placeholder",
    color: "#ffff2",
    pulse_settings: {
      phaseOneDuration: 30,
      phaseOneCharge: 2,
      postphaseInterval: 20,
      total_active_duration: {
        duration: 1000,
        unit: "milliseconds",
      },
      num_cycles: 1,
    },
  },
  {
    type: "Delay",
    src: "placeholder",
    color: "#ffff3",
    pulse_settings: {
      duration: 1300,
      unit: "seconds",
    },
  },
  {
    type: "Monophasic",
    src: "placeholder",
    color: "#ffff4",
    pulse_settings: {
      phaseOneDuration: 30,
      phaseOneCharge: 50,
      postphaseInterval: 10,
      total_active_duration: {
        duration: 2000,
        unit: "milliseconds",
      },
      num_cycles: 2,
    },
  },
];
describe("StimulationStudioProtocolViewer.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });
  afterEach(() => jest.clearAllMocks());

  test("When exiting instance, Then instance is effectively destroyed", async () => {
    const destroyed_spy = jest.spyOn(StimulationStudioProtocolViewer, "beforeDestroy");
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    wrapper.destroy();
    expect(destroyed_spy).toHaveBeenCalledWith();
  });

  test("When user wants to zoom in on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expected_scale = 80;
    await store.commit("stimulation/setZoomIn", "y-axis");
    expect(wrapper.vm.y_min_max).toBe(expected_scale);

    // should be unchanged
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(100);
  });

  test("When user wants to zoom out on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expected_scale = 180;
    await store.commit("stimulation/setZoomOut", "y-axis");
    expect(wrapper.vm.y_min_max).toBe(expected_scale);

    // should be unchanged
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(100);
  });

  test("When user wants to zoom out on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(100);

    await store.commit("stimulation/setZoomOut", "x-axis");
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(150);

    await wrapper.setData({ dynamic_plot_width: 1800 });

    await store.commit("stimulation/setZoomOut", "x-axis");
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
  });

  test("When user wants to zoom in on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(100);

    await store.commit("stimulation/setZoomIn", "x-axis");
    expect(wrapper.vm.dynamic_plot_width).toBe(1200);
    expect(wrapper.vm.x_axis_sample_length).toBe(66.66666666666667);

    await wrapper.setData({ last_x_value: 150, x_axis_sample_length: 200, datapoints: [[0, 0]] });

    await store.commit("stimulation/setZoomIn", "x-axis");
    expect(wrapper.vm.dynamic_plot_width).toBe(1800);
    expect(wrapper.vm.x_axis_sample_length).toBe(200);
  });

  test("When pulses are added to the protocol, Then the x_axis_sample_length will automatically update to be +50 unless all pulses are removed", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    expect(wrapper.vm.x_axis_sample_length).toBe(100);

    await wrapper.setData({
      last_x_value: 200,
      datapoints: [
        [0, 0],
        [0, 300],
        [200, 300],
      ],
      delayBlocks: [],
    });
    await wrapper.vm.get_dynamic_sample_length();
    expect(wrapper.vm.x_axis_sample_length).toBe(250);

    await wrapper.setData({
      last_x_value: 0,
      datapoints: [[0, 0]],
      delayBlocks: [[NaN, NaN]],
    });
    await wrapper.vm.get_dynamic_sample_length();
    expect(wrapper.vm.x_axis_sample_length).toBe(100);
  });

  test("When a user deletes the protocol, Then all datapoints should be deleted", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    wrapper.vm.datapoints = [1, 2, 3, 4];
    await store.commit("stimulation/resetState");
    expect(wrapper.vm.datapoints).toStrictEqual([]);
  });

  test("When a user adds to the protocol, Then corresponding repeat colors should be reassignment upon mutation", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    await store.dispatch("stimulation/handleProtocolOrder", test_protocol_order);
    expect(wrapper.vm.repeatColors).toBe(store.state.stimulation.repeatColors);
  });

  test("When a user adds a delay repeat to the end of the protocol, Then it will mutation to state and will automatically update in the waveform graph", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    const test_value = 5;

    await store.dispatch("stimulation/handleProtocolOrder", test_protocol_order);
    await store.dispatch("stimulation/handleNewRestDuration", test_value);

    expect(wrapper.vm.delayBlocks).toBe(store.state.stimulation.delayBlocks);
    expect(wrapper.vm.delayBlocks).toStrictEqual([[1300240, 1300245]]);
  });
  describe("StimulationStudioWaveform.vue", () => {
    test("When a user the protocol, Then all datapoints should be deleted", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      const render_spy = jest.spyOn(wrapper.vm, "render_plot");
      wrapper.vm.$options.watch.data_points.call(wrapper.vm, [
        [1, 2],
        [2, 3],
      ]);
      wrapper.vm.$options.watch.x_axis_sample_length.call(wrapper.vm, 1000);
      wrapper.vm.$options.watch.y_min.call(wrapper.vm, 0);
      wrapper.vm.$options.watch.y_max.call(wrapper.vm, 100);

      expect(render_spy).toHaveBeenCalledTimes(4);
    });

    test("When a user zooms in or zooms out of the x axis in waveform graph, Then the new graph width will be reflected and the number of the ticks of the axis will change accordingly", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      expect(wrapper.vm.frequency_of_x_ticks).toBe(10);
      expect(wrapper.vm.div__waveform_graph__dynamic_style).toStrictEqual({ width: "1280px" });
      await wrapper.setProps({ plot_area_pixel_width: 1800 });
      expect(wrapper.vm.frequency_of_x_ticks).toBe(15);
      expect(wrapper.vm.div__waveform_graph__dynamic_style).toStrictEqual({ width: "1880px" });
    });

    test("When a user hovers over a waveoform tile, Then the corresponding section of the graph will be filled with light opacity", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", test_protocol_order);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const d_points = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ data_points: d_points });

      await store.dispatch("stimulation/onPulseMouseenter", 1);

      const highlight_line_node = wrapper.find("#highlight_line_node");
      const highlight_line_path = highlight_line_node.findAll("path");

      expect(highlight_line_path).toHaveLength(1);
      expect(highlight_line_path.at(0).attributes().opacity).toBe(".15");
      expect(highlight_line_path.at(0).attributes().fill).toBe("#ffff2");
    });

    test("When a user leaves hover over a waveoform tile, Then the corresponding section of the graph will no longer be filled", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", test_protocol_order);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const d_points = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ data_points: d_points });

      await store.commit("stimulation/onPulseMouseleave");

      const highlight_line_node = wrapper.find("#highlight_line_node");
      const highlight_line_path = highlight_line_node.findAll("path");

      expect(highlight_line_path).toHaveLength(0);
    });
  });
});
