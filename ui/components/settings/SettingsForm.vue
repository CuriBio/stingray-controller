<template>
  <div>
    <div class="div__settingsform-controls">
      <span class="span__settingsform-title">Settings</span>
      <span class="span__settingsform-user-sub-title">Select&nbsp;<wbr />User</span>

      <div class="div__settingsform-editor-input">
        <InputDropDown
          :titleLabel="labelUser"
          :placeholder="keyPlaceholderUser"
          :invalidText="errorTextUser"
          :value.sync="entrykeyUser"
          :inputWidth="entryWidthUser"
          :disabled="disallowEntryUser"
          :optionsText="getUsernames"
          :messageIfInvalid="!userFound"
          :optionsId="'user-account-'"
        />
      </div>
      <div class="div__settingsform-user-edit-btn" width="88" height="45">
        <span v-show="!disableEditUser" class="span__settingsform-user-edit-btn-txt">
          <b-button
            id="edit-a-user"
            v-b-modal.edit-user
            squared
            class="w-100 h-100 edit-id"
            style="background-color: #3f3f3f; border: 0px; color: #ececed"
            >Edit&nbsp;<wbr />User
          </b-button>
          <b-modal id="edit-user" size="sm" hide-footer hide-header hide-header-close>
            <EditUser
              :dialogdata="userAccounts[userFocusIdx]"
              :openForInvalidCreds="openForInvalidCreds"
              @cancel-id="cancelUserUpdate"
              @save-id="applyUserUpdate"
              @delete-id="deleteUser"
            />
          </b-modal>
        </span>
        <span v-show="disableEditUser" class="span__settingsform-user-edit-btn-txt-disable"
          >Edit&nbsp;<wbr />User</span
        >
      </div>
    </div>
    <div class="div__settingsform-user-add-btn" width="285" height="45">
      <span class="span__settingsform-user-add-btn_txt">
        <b-button
          id="add-a-user"
          v-b-modal.add-user
          squared
          class="w-100 h-100 edit-id"
          style="background-color: #3f3f3f; border: 0px; color: #ececed"
        >
          Add&nbsp;<wbr />New&nbsp;<wbr />User</b-button
        >
        <b-modal id="add-user" size="sm" hide-footer hide-header hide-header-close>
          <AddUser @cancel-id="cancelAddingUser" @save-id="saveNewUser" />
        </b-modal>
      </span>
    </div>
    <canvas class="canvas__settings-title-separator" width="510" height="20" />
    <canvas class="canvas__settings-button-separator" width="512" height="22" />
    <div class="div__settings-tool-tip-cancel-btn" width="180" height="55" @click="cancelChanges">
      <span class="span__settings-tool-tip-cancel-btn-txt">Cancel</span>
    </div>
    <div
      class="div__settings-tool-tip-reset-btn"
      :class="[
        userFound ? 'div__settings-tool-tip-reset-btn-enable' : 'div__settings-tool-tip-reset-btn-disable',
      ]"
      width="180"
      height="55"
    >
      <span
        class="span__settings-tool-tip-reset-btn-txt"
        :class="[
          userFound
            ? 'span__settings-tool-tip-reset-btn-txt-enable'
            : 'span__settings-tool-tip-reset-btn-txt-disable',
        ]"
        @click="resetChanges()"
        >Reset&nbsp;<wbr />to&nbsp;<wbr />Defaults</span
      >
    </div>
    <div
      class="div__settings-tool-tip-save-btn"
      :class="[
        userFound ? 'div__settings-tool-tip-save-btn-enable' : 'div__settings-tool-tip-save-btn-disable',
      ]"
      width="180"
      height="55"
    >
      <canvas class="canvas__settings-tool-tip-save-btn" width="180" height="55"> </canvas>
      <span
        class="span__settings-tool-tip-save-btn-txt"
        :class="[
          userFound
            ? 'span__settings-tool-tip-save-btn-txt-enable'
            : 'span__settings-tool-tip-save-btn-txt-disable',
        ]"
        @click="saveChanges()"
        >Save&nbsp;<wbr />Changes</span
      >
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import { mapState } from "vuex";
import { library } from "@fortawesome/fontawesome-svg-core";

import { faKey } from "@fortawesome/free-solid-svg-icons";

library.add(faKey);

import BootstrapVue from "bootstrap-vue";
import { BButton } from "bootstrap-vue";
import { BModal } from "bootstrap-vue";
import { BFormInput } from "bootstrap-vue";
import AddUser from "@/components/settings/AddUser.vue";
import EditUser from "@/components/settings/EditUser.vue";
import InputDropDown from "@/components/basic-widgets/InputDropDown.vue";

Vue.use(BootstrapVue);
Vue.component("BButton", BButton);
Vue.component("BModal", BModal);
Vue.component("BFormInput", BFormInput);

export default {
  name: "SettingsForm",
  components: {
    AddUser,
    EditUser,
    InputDropDown,
  },
  data() {
    return {
      userFocusIdx: 0,
      disableEditUser: true,
      labelUser: "User Selection",
      entrykeyUser: "",
      keyPlaceholderUser: "Select User",
      errorTextUser: "An ID is required",
      entryWidthUser: 283,
      disallowEntryUser: false,
      userFound: false,
      openForInvalidCreds: false,
    };
  },
  computed: {
    ...mapState("settings", ["userAccounts", "activeUserIndex", "storedCustomerId"]),
    ...mapState("system", ["loginAttemptStatus"]),
    getUsernames: function () {
      return this.userAccounts.map((userAccount) => userAccount.username);
    },
  },
  watch: {
    entrykeyUser: function () {
      const userFocusIdx = this.getUsernames.indexOf(this.entrykeyUser);
      this.userFound = this.entrykeyUser !== "" && userFocusIdx !== -1;
      if (this.userFound) {
        this.userFocusIdx = userFocusIdx;
      }
      this.modifyBtnStates();
    },
    loginAttemptStatus: function (status) {
      if (status) {
        this.$emit("close-modal", true);
      } else if (status === false) {
        // need to check explicitly for false since null is also used
        // if login fails, prompt user to re-enter their credentials
        this.openForInvalidCreds = true;
        this.$bvModal.show("edit-user");
      } // else {
      //   this.resetChanges();
      // }
    },
  },
  created: function () {
    if (this.activeUserIndex != null) {
      this.entrykeyUser = this.userAccounts[this.activeUserIndex].username;
      this.userFocusIdx = this.activeUserIndex;
      this.disableEditUser = false;
      this.userFound = true;
    }
  },
  methods: {
    async saveChanges() {
      if (this.userFound) {
        this.$store.commit("settings/setActiveUserIndex", this.userFocusIdx);
        this.$store.commit("system/setLoginAttemptStatus", null); // set this back to null to indicate that the result is pending
        this.$store.dispatch("settings/sendLoginCommand");
      }
    },
    resetChanges() {
      this.entrykeyUser = "";
      this.$store.commit("settings/resetToDefault");
    },
    cancelChanges() {
      this.$emit("close-modal", false);
    },
    cancelAddingUser() {
      this.$bvModal.hide("add-user");
    },
    saveNewUser(newUser) {
      this.$bvModal.hide("add-user");
      this.userAccounts.push(newUser);
      this.entrykeyUser = newUser.username;
    },
    cancelUserUpdate() {
      this.$bvModal.hide("edit-user");
    },
    applyUserUpdate(editedUser) {
      this.$bvModal.hide("edit-user");
      this.openForInvalidCreds = false;
      // need to use splice so that Vue will recognize that the array was updated
      this.userAccounts.splice(this.userFocusIdx, 1, editedUser);
      this.entrykeyUser = editedUser.username;
    },
    deleteUser() {
      this.$bvModal.hide("edit-user");
      this.openForInvalidCreds = false;
      // need to use splice so that Vue will recognize that the array was updated
      this.userAccounts.splice(this.userFocusIdx, 1);
      this.userFocusIdx = 0;
      this.entrykeyUser = "";
    },
    modifyBtnStates() {
      this.disableEditUser = !this.userFound;
    },
    handleToggleState(state, label) {
      this[label] = state;
    },
  },
};
</script>
<style scoped>
.div__settingsform-controls {
  top: 0px;
  left: 0px;
  background-color: rgba(0, 0, 0);
  width: 700px;
  height: 350px;
  position: absolute;
  overflow: hidden;
  pointer-events: none;
  z-index: 2;
}

.span__settingsform-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 700px;
  height: 34px;
  top: 13px;
  left: 0px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 23px;
  color: rgb(255, 255, 255);
  text-align: center;
  z-index: 3;
  background-color: rgba(0, 0, 0);
}

.span__settingsform-user-sub-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 225px;
  height: 30px;
  top: 123.142px;
  left: calc(734.511px - 734.511px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: right;
  z-index: 21;
}

.div__settingsform-editor-input {
  pointer-events: all;
  white-space: nowrap;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  width: 285px;
  height: 45px;
  top: 70.422px;
  left: calc(962.145px - 734.511px);
  padding: 0px;
  visibility: visible;
  z-index: 55;
}

.div__settingsform-user-edit-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 88px;
  height: 45px;
  top: 112.422px;
  left: calc(1258px - 734.511px);
  visibility: visible;
  z-index: 25;
}

.span__settingsform-user-edit-btn-txt {
  padding-left: 0px;
  padding-right: 0px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 88px;
  height: 45px;
  line-height: 47px;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: rgb(236, 236, 237);
  background-color: #3f3f3f;
  z-index: 55;
}

.span__settingsform-user-edit-btn-txt-disable {
  padding-left: 0px;
  padding-right: 0px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 88px;
  height: 45px;
  line-height: 47px;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: #6e6f72;
  background-color: #3f3f3f;
  z-index: 55;
}

.div__settingsform-user-add-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 285px;
  height: 45px;
  top: 172px;
  left: calc(962.145px - 734.511px);
  visibility: visible;
  z-index: 25;
}

.span__settingsform-user-add-btn_txt {
  padding-left: 0px;
  padding-right: 0px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 285px;
  height: 45px;
  line-height: 47px;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: rgb(236, 236, 237);
  background-color: #3f3f3f;
}

.canvas__settings-title-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 510px;
  height: 1px;
  top: 56px;
  left: 95px;
  visibility: visible;
  z-index: 11;
  background-color: #878d99;
  opacity: 0.5;
}

.span__settingsform-record-file-settings {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 360px;
  height: 30px;
  top: 253px;
  left: calc(925px - 750.511px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
  z-index: 37;
}
.span__settingsform_auto-upload-settings {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 232px;
  height: 30px;
  top: 291px;
  left: calc(1026px - 775.511px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: left;
  z-index: 41;
}
.div__settingsform-toggle-icon {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 62px;
  height: 34px;
  top: 293px;
  left: calc(961px - 775.511px);
  visibility: visible;
  z-index: 57;
  color: white;
}

.div__settingsform-dropdown {
  pointer-events: all;
  transform: rotate(0deg);
  /* overflow: hidden; */
  position: absolute;
  width: 80px;
  height: 34px;
  top: 327px;
  left: calc(961px - 566px);
  visibility: visible;
  z-index: 57;
  color: white;
}

.div__settingsform-toggle-icon-2 {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 62px;
  height: 34px;
  top: 364px;
  left: calc(961px - 775.511px);
  visibility: visible;
  z-index: 45;
}

.div__settingsform-toggle-icon-3 {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 62px;
  height: 34px;
  top: 399px;
  left: calc(961px - 775.511px);
  visibility: visible;
  z-index: 45;
}

.div__settings-tool-tip-cancel-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 180px;
  height: 55px;
  top: 275px;
  left: 450px;
  visibility: visible;
  z-index: 55;
  background-color: rgb(183, 183, 183);
}
.span__settings-tool-tip-cancel-btn-txt {
  padding-left: 5px;
  padding-right: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 170px;
  height: 45px;
  line-height: 47px;
  top: 5px;
  left: 5px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: rgb(0, 0, 0);
  z-index: 55;
}
.div__settings-tool-tip-reset-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 180px;
  height: 55px;
  top: 275px;
  left: 260px;
  visibility: visible;
  z-index: 55;
  background-color: #b7b7b7c9;
}
.span__settings-tool-tip-reset-btn-txt {
  padding-left: 5px;
  padding-right: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 170px;
  height: 45px;
  line-height: 47px;
  top: 5px;
  left: 5px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
}
.div__settings-tool-tip-save-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 180px;
  height: 55px;
  top: 275px;
  left: 70px;
  visibility: visible;
  z-index: 55;
}
.div__settings-tool-tip-save-btn-enable,
.div__settings-tool-tip-reset-btn-enable {
  background-color: rgb(183, 183, 183);
}

.div__settings-tool-tip-save-btn-disable,
.div__settings-tool-tip-reset-btn-disable {
  background-color: #b7b7b7c9;
}

.div__settings-tool-tip-save-btn-enable:hover {
  background-color: #19ac8a;
  cursor: pointer;
}

.div__settings-tool-tip-reset-btn-enable:hover,
.div__settings-tool-tip-cancel-btn:hover {
  background-color: #b7b7b7c9;
  cursor: pointer;
}

.canvas__settings-tool-tip-save-btn {
  -webkit-transform: translateZ(0);
  position: absolute;
  width: 180px;
  height: 55px;
  top: 0px;
  left: 0px;
}
.span__settings-tool-tip-save-btn-txt {
  padding-left: 5px;
  padding-right: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 170px;
  height: 45px;
  line-height: 47px;
  top: 5px;
  left: 5px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
}

.span__settings-tool-tip-save-btn-txt-disable,
.span__settings-tool-tip-reset-btn-txt-disable {
  color: #6e6f72;
}

.span__settings-tool-tip-reset-btn-txt-enable,
.span__settings-tool-tip-save-btn-txt-enable {
  color: rgb(0, 0, 0);
}

.canvas__settings-button-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 512px;
  height: 1px;
  top: 250px;
  left: 95px;
  visibility: visible;
  background-color: #878d99;
  opacity: 0.5;
  z-index: 33;
}

.modal-backdrop {
  background-color: rgb(0, 0, 0, 0.5);
}

.modal {
  position: fixed;
  top: 15%;
  left: -25%;
}

.btn {
  padding-bottom: 0;
  padding-left: 0;
  padding-right: 0;
  padding-top: 0;
}

.form-control {
  padding-bottom: 12px;
  padding-left: 12px;
  padding-right: 12px;
  padding-top: 12px;
  display: inline-block;
}

.form-control:focus {
  border: none;
  box-shadow: none;
  -webkit-box-shadow: none;
}

datalist {
  display: none;
  background: #2f2f2f;
  font: 17px Muli;
  color: #ececed;
}
#add-user,
#edit-user,
#add-user,
#edit-user {
  position: fixed;
  margin: 5% auto;
  top: 15%;
  left: 0;
  right: 0;
}
</style>
