export const TEST_BIPHASIC_PULSE_SETTINGS = {
  phaseOneDuration: "",
  phaseOneCharge: "",
  interphaseInterval: "",
  phaseTwoDuration: "",
  phaseTwoCharge: "",
  postphaseInterval: "",
  totalActiveDuration: {
    duration: "",
    unit: "milliseconds",
  },
  numCycles: 0,
  frequency: "",
};

export const TEST_MONOPHASIC_PULSE_SETTINGS = {
  phaseOneDuration: "",
  phaseOneCharge: "",
  postphaseInterval: "",
  totalActiveDuration: {
    duration: "",
    unit: "milliseconds",
  },
  numCycles: 0,
  frequency: "",
};

export const MONOPHASIC_DROP_ELEMENT = {
  type: "Monophasic",
  color: "",
  pulseSettings: TEST_MONOPHASIC_PULSE_SETTINGS,
  subprotocols: [],
};

export const BIPHASIC_DROP_ELEMENT = {
  type: "Biphasic",
  color: "",
  pulseSettings: TEST_BIPHASIC_PULSE_SETTINGS,
  subprotocols: [],
};

export const VALID_STIM_JSON = JSON.stringify({
  protocols: [
    {
      color: "hsla(51, 90%, 40%, 1)",
      letter: "A",
      label: "",
      protocol: {
        name: "testProto_1",
        runUntilStopped: true,
        stimulationType: "C",
        restDuration: 0,
        timeUnit: "milliseconds",
        subprotocols: [
          {
            type: "Delay",
            duration: 333,
            unit: "milliseconds",
          },
        ],
        detailedSubprotocols: [
          {
            type: "Delay",
            color: "hsla(69, 92%, 45%, 1)",
            pulseSettings: {
              duration: 333,
              unit: "milliseconds",
            },
            subprotocols: [],
          },
        ],
      },
    },
    {
      color: "hsla(334, 95%, 53%, 1)",
      letter: "B",
      label: "",
      protocol: {
        name: "testProto_2",
        runUntilStopped: true,
        stimulationType: "C",
        restDuration: 0,
        timeUnit: "milliseconds",
        subprotocols: [
          {
            type: "Delay",
            duration: 15000,
            unit: "milliseconds",
          },
        ],
        detailedSubprotocols: [
          {
            type: "Delay",
            color: "hsla(69, 92%, 45%, 1)",
            pulseSettings: {
              duration: 15000,
              unit: "milliseconds",
            },
            subprotocols: [],
          },
        ],
      },
    },
  ],
  protocolAssignments: {
    A1: null,
    B1: null,
    C1: null,
    D1: null,
    A2: null,
    B2: null,
    C2: null,
    D2: null,
    A3: null,
    B3: null,
    C3: null,
    D3: null,
    A4: "B",
    B4: "B",
    C4: "B",
    D4: "B",
    A5: "A",
    B5: "A",
    C5: "A",
    D5: "A",
    A6: null,
    B6: null,
    C6: null,
    D6: null,
  },
});

export const INVALID_STIM_JSON = JSON.stringify({
  protocols: [
    {
      color: "hsla(51, 90%, 40%, 1)",
      letter: "A",
      label: "",
      protocol: {
        name: "testProto_1",
        runUntilStopped: true,
        stimulationType: "C",
        restDuration: 0,
        timeUnit: "milliseconds",
        subprotocols: [
          {
            type: "Delay",
            duration: 0,
            unit: "milliseconds",
          },
        ],
        detailedSubprotocols: [
          {
            type: "Delay",
            color: "hsla(69, 92%, 45%, 1)",
            pulseSettings: {
              duration: 0,
              unit: "milliseconds",
            },
            subprotocols: [],
          },
        ],
      },
    },
    {
      color: "hsla(334, 95%, 53%, 1)",
      letter: "B",
      label: "",
      protocol: {
        name: "testProto_2",
        runUntilStopped: true,
        stimulationType: "C",
        restDuration: 0,
        timeUnit: "milliseconds",
        subprotocols: [
          {
            type: "Biphasic",
            phaseOneDuration: 0,
            phaseOneCharge: 200,
            interphaseInterval: 10,
            phaseTwoDuration: 3,
            phaseTwoCharge: 200,
            postphaseInterval: 5,
            totalActiveDuration: {
              duration: 1000,
              unit: "milliseconds",
            },
            numCycles: 1,
          },
        ],
        detailedSubprotocols: [
          {
            type: "Biphasic",
            color: "hsla(69, 92%, 45%, 1)",
            pulseSettings: {
              phaseOneDuration: 100,
              phaseOneCharge: 200,
              interphaseInterval: 10,
              phaseTwoDuration: 3,
              phaseTwoCharge: 200,
              postphaseInterval: 5,
              totalActiveDuration: {
                duration: 1000,
                unit: "milliseconds",
              },
              numCycles: 1,
            },
            subprotocols: [],
          },
        ],
      },
    },
    {
      color: "hsla(310, 95%, 53%, 1)",
      letter: "C",
      label: "",
      protocol: {
        name: "testProto_3",
        runUntilStopped: true,
        stimulationType: "C",
        restDuration: 0,
        timeUnit: "milliseconds",
        subprotocols: [
          {
            type: "Monophasic",
            phaseOneDuration: 10,
            phaseOneCharge: 0,
            postphaseInterval: 5,
            totalActiveDuration: {
              duration: 1,
              unit: "seconds",
            },
            numCycles: 1,
          },
        ],
        detailedSubprotocols: [
          {
            type: "Monophasic",
            color: "hsla(69, 92%, 45%, 1)",
            pulseSettings: {
              phaseOneDuration: 10,
              phaseOneCharge: 0,
              postphaseInterval: 5,
              totalActiveDuration: {
                duration: 1,
                unit: "seconds",
              },
              numCycles: 1,
            },
            subprotocols: [],
          },
        ],
      },
    },
  ],
  protocolAssignments: {
    A1: null,
    B1: null,
    C1: null,
    D1: null,
    A2: null,
    B2: null,
    C2: null,
    D2: null,
    A3: null,
    B3: null,
    C3: null,
    D3: null,
    A4: "B",
    B4: "B",
    C4: "B",
    D4: "B",
    A5: "A",
    B5: "A",
    C5: "A",
    D5: "A",
    A6: "C",
    B6: "C",
    C6: null,
    D6: null,
  },
});

export const TEST_PROTOCOL_ORDER = [
  {
    type: "Biphasic",
    src: "test",
    color: "b7b7b7",
    pulseSettings: {
      phaseOneDuration: 100,
      phaseOneCharge: 200,
      interphaseInterval: 10,
      phaseTwoDuration: 3,
      phaseTwoCharge: 200,
      postphaseInterval: 5,
      totalActiveDuration: {
        duration: 1000,
        unit: "milliseconds",
      },
      numCycles: 1,
    },
    subprotocols: [],
  },
];

export const TEST_PROTOCOL_ORDER_2 = [
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
    subprotocols: [],
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
    subprotocols: [],
  },
  {
    type: "Delay",
    src: "placeholder",
    color: "#ffff3",
    pulseSettings: {
      duration: 1300,
      unit: "seconds",
    },
    subprotocols: [],
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
    subprotocols: [],
  },
];

export const TEST_PROTOCOL_LIST = [
  { letter: "", color: "", label: "Create New" },
  {
    letter: "A",
    color: "#118075",
    label: "Tester",
    protocol: {
      name: "Tester",
      stimulationType: "C",
      restDuration: 20,
      timeUnit: "milliseconds",
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
          nestedProtocols: [],
          color: "hsla(99, 60%, 40%, 1)",
          pulseSettings: { duration: 15, unit: "seconds" },
          subprotocols: [],
        },
      ],
    },
  },
];

export const TEST_PROTOCOL_B = {
  letter: "B",
  color: "#000000",
  label: "test_1",
  protocol: {
    stimulationType: "C",
    runUntilStopped: true,
    subprotocols: [
      {
        type: "Monophasic",
        phaseOneDuration: 15,
        phaseOneCharge: 500,
        postphaseInterval: 3,
        numCycles: 1,
      },
    ],
    detailedSubprotocols: [
      {
        color: "hsla(45, 90%, 40%, 1)",
        subprotocols: [],
      },
    ],
  },
};
export const TEST_PROTOCOL_D = {
  letter: "D",
  color: "#000001",
  label: "test_2",
  protocol: {
    stimulationType: "C",
    runUntilStopped: false,
    subprotocols: [
      {
        type: "Biphasic",
        phaseOneDuration: 20,
        phaseOneCharge: 400,
        interphaseInterval: 10,
        phaseTwoCharge: -400,
        phaseTwoDuration: 20,
        postphaseInterval: 0,
        numCycles: 2,
      },
    ],
    detailedSubprotocols: [
      {
        color: "hsla(309, 50%, 60%, 1)",
        subprotocols: [],
      },
    ],
  },
};

export const TEST_PROTOCOL_ORDER_3 = [
  {
    type: "Biphasic",
    src: "placeholder",
    runUntilStopped: false,
    color: "hsla(15, 100%, 50%, 1)",
    pulseSettings: {
      phaseOneDuration: 20,
      phaseOneCharge: 2,
      interphaseInterval: 10,
      phaseTwoDuration: 20,
      phaseTwoCharge: -5,
      postphaseInterval: 0,
      totalActiveDuration: {
        duration: 1000,
        unit: "milliseconds",
      },
      numCycles: 1,
      frequency: 3,
    },
  },
  {
    type: "Monophasic",
    src: "placeholder",
    runUntilStopped: false,
    color: "hsla(205, 100%, 50%, 1)",
    pulseSettings: {
      phaseOneDuration: 20,
      phaseOneCharge: 3,
      postphaseInterval: 0,
      totalActiveDuration: {
        duration: 2000,
        unit: "milliseconds",
      },
      numCycles: 2,
      frequency: 1,
    },
    subprotocols: [],
  },
  {
    type: "Delay",
    src: "placeholder",
    runUntilStopped: false,
    color: "hsla(5, 100%, 50%, 1)",
    pulseSettings: {
      duration: 300,
      unit: "seconds",
    },
    subprotocols: [],
  },
  {
    type: "Monophasic",
    src: "placeholder",
    runUntilStopped: false,
    color: "hsla(190, 100%, 50%, 1)",
    pulseSettings: {
      phaseOneDuration: 10,
      phaseOneCharge: 2,
      postphaseInterval: 0,
      totalActiveDuration: {
        duration: 4000,
        unit: "milliseconds",
      },
      numCycles: 4,
      frequency: 5,
    },
    subprotocols: [],
  },
];

export const TEST_PROTOCOL_LIST_2 = [
  { letter: "", color: "", label: "Create New" },
  {
    letter: "A",
    color: "#118075",
    label: "Tester",
    protocol: {
      name: "Tester",
      stimulationType: "C",
      runUntilStopped: false,
      restDuration: 20,
      timeUnit: "milliseconds",
      subprotocols: [
        {
          type: "Delay",
          duration: 15000,
          unit: "milliseconds",
        },
        {
          type: "Delay",
          duration: 20,
          unit: "seconds",
        },
      ],
      detailedSubprotocols: [
        {
          type: "Delay",
          src: "/delay-tile.png",
          runUntilStopped: false,
          color: "hsla(65, 100%, 50%, 1)",
          pulseSettings: {
            pduration: 15000,
            unit: "milliseconds",
          },
          subprotocols: [],
        },
      ],
    },
  },
];

export const INCOMPATIBLE_PROTOCOL_EXPORT_MULTI = {
  protocols: [
    {
      color: "hsla(281, 99%, 56%, 1)",
      letter: "A",
      label: "",
      protocol: {
        name: "Export Protocol",
        stop_setting: "Stimulate Until Stopped",
        stimulation_type: "C",
        rest_duration: 0,
        time_unit: "milliseconds",
        pulses: [
          {
            phase_one_duration: 1000,
            phase_one_charge: 0,
            interphase_interval: 0,
            phase_two_duration: 0,
            phase_two_charge: 0,
            repeat_delay_interval: 0,
            total_active_duration: 1000,
          },
          {
            phase_one_duration: 10,
            phase_one_charge: 100,
            interphase_interval: 0,
            phase_two_duration: 0,
            phase_two_charge: 0,
            repeat_delay_interval: 90,
            total_active_duration: 1000,
          },
          {
            phase_one_duration: 10,
            phase_one_charge: 100,
            interphase_interval: 0,
            phase_two_duration: 10,
            phase_two_charge: -100,
            repeat_delay_interval: 980,
            total_active_duration: 2000,
          },
        ],
        detailed_pulses: [
          {
            type: "Delay",
            repeat: { color: "hsla(281, 91%, 41%, 1)", number_of_repeats: 1 },
            pulse_settings: {
              phase_one_duration: 1000,
              phase_one_charge: 0,
              interphase_interval: 0,
              phase_two_duration: 0,
              phase_two_charge: 0,
            },
            stim_settings: {
              repeat_delay_interval: 0,
              total_active_duration: { duration: 1000, unit: "milliseconds" },
            },
          },
          {
            type: "Monophasic",
            repeat: { color: "hsla(253, 99%, 58%, 1)", number_of_repeats: 10 },
            pulse_settings: {
              phase_one_duration: 10,
              phase_one_charge: 100,
              interphase_interval: 0,
              phase_two_duration: 0,
              phase_two_charge: 0,
            },
            stim_settings: {
              repeat_delay_interval: 90,
              total_active_duration: { duration: 1000, unit: "milliseconds" },
            },
          },
          {
            type: "Biphasic",
            repeat: { color: "hsla(11, 99%, 55%, 1)", number_of_repeats: 1 },
            pulse_settings: {
              phase_one_duration: 10,
              phase_one_charge: 100,
              interphase_interval: 0,
              phase_two_duration: 10,
              phase_two_charge: -100,
            },
            stim_settings: {
              repeat_delay_interval: 980,
              total_active_duration: { duration: 2000, unit: "milliseconds" },
            },
          },
        ],
      },
    },
  ],
  protocol_assignments: {
    A1: null,
    B1: null,
    C1: null,
    D1: null,
    A2: null,
    B2: null,
    C2: null,
    D2: null,
    A3: null,
    B3: null,
    C3: null,
    D3: null,
    A4: null,
    B4: null,
    C4: null,
    D4: null,
    A5: null,
    B5: null,
    C5: null,
    D5: null,
    A6: null,
    B6: null,
    C6: null,
    D6: null,
  },
};
