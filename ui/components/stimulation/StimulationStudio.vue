<template>
  <div>
    <div class="div__stimulationstudio-layout-background">
      <span class="span__stimulationstudio-header-label">Stimulation Studio</span>
      <StimulationStudioWidget class="stimulationstudio_widget-container" />
      <StimulationStudioCreateAndEdit
        class="stimulationstudio_createandedit-container"
        :disablEdits="disableEdits"
        @handle-selection-change="handleSelectionChange"
      />
      <StimulationStudioDragAndDropPanel
        class="stimulationstudio_draganddroppanel-container"
        :disableEdits="disableEdits"
      />
      <StimulationStudioBlockViewEditor
        class="stimulationstudio_blockvieweditor-container"
        @rest-duration-validity="setNewRestDuration"
      />
      <StimulationStudioProtocolViewer class="stimulationstudio_protocolviewer-container" />
      <div class="button-background">
        <div v-for="(value, idx) in btnLabels" :id="value" :key="value" @click.exact="handleClick(idx)">
          <div v-b-popover.hover.top="btnHover" :class="getBtnClass(idx)">
            <span :class="getBtnLabelClass(idx)">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="isInOfflineMode" class="div__stimulationstudio-overlay" />
  </div>
</template>
<script>
import StimulationStudioCreateAndEdit from "@/components/stimulation/StimulationStudioCreateAndEdit.vue";
import StimulationStudioWidget from "@/components/stimulation/StimulationStudioWidget.vue";
import StimulationStudioDragAndDropPanel from "@/components/stimulation/StimulationStudioDragAndDropPanel.vue";
import StimulationStudioBlockViewEditor from "@/components/stimulation/StimulationStudioBlockViewEditor.vue";
import StimulationStudioProtocolViewer from "@/components/stimulation/StimulationStudioProtocolViewer.vue";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import { SYSTEM_STATUS } from "@/store/modules/system/enums";

import { mapState } from "vuex";

/**
 * @vue-data {Array} btnLabels - button labels for base of stim studio component
 * @vue-data {Object} selectedProtocol - Current selected protocol from drop down in CreateAndEdit component
 * @vue-data {Boolean} restDurIsValid - State of validity of current rest duration for protocol
 * @vue-computed {Boolean} disableEdits - Boolean to conditionally check if stim is active
 * @vue-computed {Object} btnHover - Handle tooltip text based off is stim is currently active
 * @vue-computed {Boolean} stimulationType - Conditionally expand type of stimulation based on state
 * @vue-event {Event} handleClick - Handles what gets executed when any of the base buttons are selected
 * @vue-event {Event} setNewRestDuration - Set validity of new rest duration in stim studio
 * @vue-event {Event} getBtnClass - Get dynamic button class based on disabled state
 * @vue-event {Event} getBtnLabelClass - Get dynamic button label class based on disabled state
 * @vue-event {Event} handleSelectionChanged - Gets emitted when a user selected a protocol for edit so it can be used if new changes need to be discarded
 */

export default {
  name: "StimulationStudio",
  components: {
    StimulationStudioWidget,
    StimulationStudioCreateAndEdit,
    StimulationStudioDragAndDropPanel,
    StimulationStudioBlockViewEditor,
    StimulationStudioProtocolViewer,
  },
  data() {
    return {
      btnLabels: ["Save Changes", "Clear/Reset All", "Discard Changes"],
      selectedProtocol: { label: "Create New", color: "", letter: "" },
      restDurIsValid: true,
    };
  },
  computed: {
    ...mapState("stimulation", ["stimStatus", "protocolEditor"]),
    ...mapState("system", ["statusUuid"]),
    disableEdits: function () {
      return this.stimStatus === STIM_STATUS.STIM_ACTIVE;
    },
    btnHover: function () {
      return {
        content: "Cannot make changes to stim settings while actively stimulating",
        disabled: !this.disableEdits,
      };
    },
    isInOfflineMode: function () {
      // disable if going offline or in offline
      return [SYSTEM_STATUS.OFFLINE_STATE, SYSTEM_STATUS.GOING_OFFLINE_STATE].includes(this.statusUuid);
    },
  },
  methods: {
    async handleClick(idx) {
      if (this.disableEdits) {
        return;
      }

      if (idx === 0) {
        await this.$store.dispatch("stimulation/addSavedPotocol");
        this.$store.dispatch("stimulation/handleProtocolEditorReset");
        this.selectedProtocol = { label: "Create New", color: "", letter: "" };
      } else if (idx === 1) {
        this.$store.commit("stimulation/resetState");
      } else if (idx === 2) {
        if (this.selectedProtocol.label === "Create New") {
          this.$store.commit("stimulation/resetProtocolEditor");
        } else {
          this.$store.dispatch("stimulation/editSelectedProtocol", this.selectedProtocol);
        }
      }
    },
    setNewRestDuration(isValid) {
      this.restDurIsValid = isValid;
    },

    handleSelectionChange(protocol) {
      this.selectedProtocol = protocol;
    },
    getBtnClass(idx) {
      return this.disableEdits || (idx === 0 && !this.restDurIsValid)
        ? "btn-container-disable"
        : "btn-container";
    },
    getBtnLabelClass(idx) {
      return this.disableEdits || (idx === 0 && !this.restDurIsValid) ? "btn-label-disable" : "btn-label";
    },
  },
};
</script>

<style scoped>
body {
  user-select: none;
}

.div__stimulationstudio-layout-background {
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(0, 0, 0);
  position: absolute;
  width: 1629px;
  height: 885px;
}

.span__stimulationstudio-header-label {
  pointer-events: all;
  align-self: center;
  line-height: 100%;
  position: relative;
  transform: rotate(0deg);
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-size: 23px;
  width: 658px;
  height: 24px;
  top: 20px;
  left: 200px;
  color: rgb(255, 255, 255);
  text-align: center;
}

.button-background {
  width: 60%;
  display: flex;
  justify-content: center;
  left: 10%;
  top: 93%;
  height: 60px;
  position: absolute;
}

.btn-container-disable {
  display: flex;
  justify-content: center;
  align-content: center;
  position: relative;
  width: 90%;
  height: 45px;
  margin: 0 40px 0 40px;
  background: #b7b7b7c9;
}

.btn-container {
  display: flex;
  justify-content: center;
  align-content: center;
  position: relative;
  width: 90%;
  height: 45px;
  margin: 0 40px 0 40px;
  background: #b7b7b7;
}

.btn-container:hover {
  background: #b7b7b7c9;
  cursor: pointer;
}

.btn-label {
  transform: translateZ(0px);
  line-height: 45px;
  font-family: Muli;
  font-size: 16px;
  color: rgb(0, 0, 0);
}

.btn-label-disable {
  transform: translateZ(0px);
  line-height: 45px;
  font-family: Muli;
  font-size: 16px;
  color: #6e6f72;
}

.stimulationstudio_widget-container {
  top: 77px;
  left: 132px;
}

.stimulationstudio_createandedit-container {
  top: 77px;
  left: 563px;
}

.stimulationstudio_draganddroppanel-container {
  top: 0px;
}

.stimulationstudio_blockvieweditor-container {
  top: 375px;
  left: 6px;
}

.stimulationstudio_protocolviewer-container {
  top: 570px;
  left: 6px;
}

.div__stimulationstudio-overlay {
  width: 1629px;
  height: 885px;
  position: absolute;
  top: 0;
  background: rgb(0, 0, 0);
  z-index: 100;
  opacity: 0.5;
}
</style>
