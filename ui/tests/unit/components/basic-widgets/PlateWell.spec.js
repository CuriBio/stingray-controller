import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/basic-widgets/PlateWell.vue";
import { PlateWell as DistComponentToTest } from "@/dist/mantarray.common";
// import { shallowMount } from "@vue/test-utils";

import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("PlateWell.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When mounting PlateWell from the build dist file, Then it loads successfully", async () => {
    const propsData = {
      classname: "plate",
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 0,
    };
    const wrapper = mount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const well = wrapper.findAll("circle");
    expect(well).toHaveLength(1);
  });
  test("When the PlateWell is mounted, Then mouseenter event on the circle would emit and event 'enter-well' with plate index range [0..23]", async () => {
    const propsData = {
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 0,
    };
    const wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const plate = wrapper.find(".well");

    await plate.trigger("mouseenter");
    const enterWellEvents = wrapper.emitted("enter-well");
    expect(enterWellEvents).toHaveLength(1);
    expect(enterWellEvents[0]).toStrictEqual([0]);
  });
  test("When the PlateWell is mounted, Then mouseleave event on the circle would emit and event 'leave-well' with plate index range [0..23]", async () => {
    const propsData = {
      classname: "plate",
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 1,
    };
    const wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const plate = wrapper.find(".well");

    await plate.trigger("mouseleave");
    const leaveWellEvents = wrapper.emitted("leave-well");
    expect(leaveWellEvents).toHaveLength(1);
    expect(leaveWellEvents[0]).toStrictEqual([1]);
  });

  test("When the PlateWell is mounted, Then click event on the circle would emit and event 'click-exact' with plate index range [0..23]", async () => {
    const propsData = {
      classname: "plate",
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 1,
    };
    const wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const plate = wrapper.find(".well");

    await plate.trigger("click");
    const clickWellEvents = wrapper.emitted("click-exact");
    expect(clickWellEvents).toHaveLength(1);
    expect(clickWellEvents[0]).toStrictEqual([1]);
  });

  test("When the PlateWell is mounted, Then click+shift event on the circle would emit and event 'click-shift-exact' with plate index range [0..23]", async () => {
    const propsData = {
      classname: "plate",
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 5,
    };
    const wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const plate = wrapper.find(".well");

    await plate.trigger("click", {
      shiftKey: true, // For testing @click.shift handlers
    });
    await wrapper.vm.$nextTick(); // wait for update
    const clickWellEvents = wrapper.emitted("click-shift-exact");
    expect(clickWellEvents).toHaveLength(1);
    expect(clickWellEvents[0]).toStrictEqual([5]);
  });

  test("When the PlateWell is mounted, Then click+ctrl event on the circle would emit and event 'click-ctrl-exact' with plate index range [0..23]", async () => {
    const propsData = {
      classname: "plate",
      svgHeight: 100,
      svgWidth: 100,
      circleX: 50,
      circleY: 50,
      radius: 50,
      strk: "#ececed",
      strokeWdth: 0,
      plateFill: "#b7b7b7",
      index: 10,
    };
    const wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const plate = wrapper.find(".well");

    await plate.trigger("click", {
      ctrlKey: true, // For testing @click.ctrl handlers
    });
    await wrapper.vm.$nextTick(); // wait for update
    const clickWellEvents = wrapper.emitted("click-ctrl-exact");
    expect(clickWellEvents).toHaveLength(1);
    expect(clickWellEvents[0]).toStrictEqual([10]);
  });
});
