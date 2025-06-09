import * as pbi from "powerbi-client";

export function embedReport(container, embedUrl, embedToken) {
  const config = {
    type: 'report',
    tokenType: pbi.models.TokenType.Embed,
    accessToken: embedToken,
    embedUrl: embedUrl,
    settings: {
      panes: { filters: { visible: false } }
    }
  };
  pbi.powerbi.createReport(container, config);
}