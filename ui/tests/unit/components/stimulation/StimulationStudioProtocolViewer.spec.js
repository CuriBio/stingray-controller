import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioProtocolViewer from "@/components/stimulation/StimulationStudioProtocolViewer.vue";
import StimulationStudioWaveform from "@/components/stimulation/StimulationStudioWaveform.vue";
import Vuex from "vuex";
import { convertXYArraysToD3Array } from "@/js-utils/WaveformDataFormatter.js";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

const testProtocolOrder = [
  {
    type: "Biphasic",
    src: "placeholder",
    color: "#ffff1",
    pulseSettings: {
      phaseOneDuration: 30,
      phaseOneCharge: 20,
      interphaseInterval: 5,
      phaseTwoDuration: 10,
      phaseTwoCharge: -5,
      postphaseInterval: 10,
      totalActiveDuration: {
        duration: 2000,
        unit: "milliseconds",
      },
      numCycles: 2,
    },
  },
  {
    type: "Monophasic",
    src: "placeholder",
    color: "#ffff2",
    pulseSettings: {
      phaseOneDuration: 30,
      phaseOneCharge: 2,
      postphaseInterval: 20,
      totalActiveDuration: {
        duration: 1000,
        unit: "milliseconds",
      },
      numCycles: 1,
    },
  },
  {
    type: "Delay",
    src: "placeholder",
    color: "#ffff3",
    pulseSettings: {
      duration: 1300,
      unit: "seconds",
    },
  },
  {
    type: "Monophasic",
    src: "placeholder",
    color: "#ffff4",
    pulseSettings: {
      phaseOneDuration: 30,
      phaseOneCharge: 50,
      postphaseInterval: 10,
      totalActiveDuration: {
        duration: 2000,
        unit: "milliseconds",
      },
      numCycles: 2,
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
    const destroyedSpy = jest.spyOn(StimulationStudioProtocolViewer, "beforeDestroy");
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    wrapper.destroy();
    expect(destroyedSpy).toHaveBeenCalledWith();
  });

  test("When user wants to zoom in on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expectedScale = 80;
    await store.commit("stimulation/setZoomIn", "y-axis");
    expect(wrapper.vm.yMinMax).toBe(expectedScale);

    // should be unchanged
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
  });

  test("When user wants to zoom out on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expectedScale = 180;
    await store.commit("stimulation/setZoomOut", "y-axis");
    expect(wrapper.vm.yMinMax).toBe(expectedScale);

    // should be unchanged
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
  });

  test("When user wants to zoom out on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);

    await store.commit("stimulation/setZoomOut", "x-axis");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(150);

    await wrapper.setData({ dynamicPlotWidth: 1800 });

    await store.commit("stimulation/setZoomOut", "x-axis");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
  });

  test("When user wants to zoom in on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);

    await store.commit("stimulation/setZoomIn", "x-axis");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(66.66666666666667);

    await wrapper.setData({ lastXValue: 150, xAxisSampleLength: 200, datapoints: [[0, 0]] });

    await store.commit("stimulation/setZoomIn", "x-axis");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1800);
    expect(wrapper.vm.xAxisSampleLength).toBe(200);
  });

  test("When pulses are added to the protocol, Then the xAxisSampleLength will automatically update to be +50 unless all pulses are removed", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    expect(wrapper.vm.xAxisSampleLength).toBe(100);

    await wrapper.setData({
      lastXValue: 200,
      datapoints: [
        [0, 0],
        [0, 300],
        [200, 300],
      ],
      delayBlocks: [],
    });
    await wrapper.vm.getDynamicSampleLength();
    expect(wrapper.vm.xAxisSampleLength).toBe(250);

    await wrapper.setData({
      lastXValue: 0,
      datapoints: [[0, 0]],
      delayBlocks: [[NaN, NaN]],
    });
    await wrapper.vm.getDynamicSampleLength();
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
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

    await store.dispatch("stimulation/handleProtocolOrder", testProtocolOrder);
    expect(wrapper.vm.repeatColors).toBe(store.state.stimulation.repeatColors);
  });

  test("When a user adds a delay repeat to the end of the protocol, Then it will mutation to state and will automatically update in the waveform graph", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    const testValue = 5;

    await store.dispatch("stimulation/handleProtocolOrder", testProtocolOrder);
    await store.dispatch("stimulation/handleNewRestDuration", testValue);

    expect(wrapper.vm.delayBlocks).toBe(store.state.stimulation.delayBlocks);
    expect(wrapper.vm.delayBlocks).toStrictEqual([[1300240, 1300245]]);
  });
  describe("StimulationStudioWaveform.vue", () => {
    test("When a user the protocol, Then all datapoints should be deleted", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      const renderSpy = jest.spyOn(wrapper.vm, "renderPlot");
      wrapper.vm.$options.watch.dataPoints.call(wrapper.vm, [
        [1, 2],
        [2, 3],
      ]);
      wrapper.vm.$options.watch.xAxisSampleLength.call(wrapper.vm, 1000);
      wrapper.vm.$options.watch.yMin.call(wrapper.vm, 0);
      wrapper.vm.$options.watch.yMax.call(wrapper.vm, 100);

      expect(renderSpy).toHaveBeenCalledTimes(4);
    });

    test("When a user zooms in or zooms out of the x axis in waveform graph, Then the new graph width will be reflected and the number of the ticks of the axis will change accordingly", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      expect(wrapper.vm.frequencyOfXTicks).toBe(10);
      expect(wrapper.vm.div__waveformGraph__dynamicStyle).toStrictEqual({ width: "1280px" });
      await wrapper.setProps({ plotAreaPixelWidth: 1800 });
      expect(wrapper.vm.frequencyOfXTicks).toBe(15);
      expect(wrapper.vm.div__waveformGraph__dynamicStyle).toStrictEqual({ width: "1880px" });
    });

    test("When a user hovers over a waveoform tile, Then the corresponding section of the graph will be filled with light opacity", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", testProtocolOrder);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const dPoints = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ dataPoints: dPoints });

      await store.dispatch("stimulation/onPulseMouseenter", 1);

      const highlightLineNode = wrapper.find("#highlightLineNode");
      const highlightLinePath = highlightLineNode.findAll("path");

      expect(highlightLinePath).toHaveLength(1);
      expect(highlightLinePath.at(0).attributes().opacity).toBe(".15");
      expect(highlightLinePath.at(0).attributes().fill).toBe("#ffff2");
    });

    test("When a user leaves hover over a waveoform tile, Then the corresponding section of the graph will no longer be filled", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", testProtocolOrder);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const dPoints = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ dataPoints: dPoints });

      await store.commit("stimulation/onPulseMouseleave");

      const highlightLineNode = wrapper.find("#highlightLineNode");
      const highlightLinePath = highlightLineNode.findAll("path");

      expect(highlightLinePath).toHaveLength(0);
    });
  });
});
