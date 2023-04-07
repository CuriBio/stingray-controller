export default {
  async sendLoginCommand() {
    const { activeUserIndex, userAccounts } = this.state.settings;
    const { customerId, userPassword, userName } = userAccounts[activeUserIndex];

    const params = {
      command: "login",
      customer_id: customerId,
      user_name: userName,
      user_password: userPassword,
    };

    this.state.system.socket.send(JSON.stringify(params));
  },
};
