export default {
  async sendLoginCommand(_, userDetails) {
    const { customerId, password, username } = userDetails;

    const params = {
      command: "login",
      customer_id: customerId,
      username,
      password,
    };

    this.state.system.socket.send(JSON.stringify(params));
  },
};
