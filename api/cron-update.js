// Vercel Serverless Function: Cron Update Hook
const liveHandler = require('./live');

module.exports = async (req, res) => {
  return liveHandler(req, res);
};
