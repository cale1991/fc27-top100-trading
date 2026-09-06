export type Opportunity = {
  id: string; card_id: string; card: string; card_version: string; rating?: number | null;
  action: string; rank?: number | null; status: string; reference_price?: number | null; reference_source?: string | null;
  reference_age_seconds?: number | null; reference_timestamp?: string | null; reference_uncertainty_pct?: number | null;
  latest_execution_price?: number | null; max_buy_price?: number | null; target_sell_low?: number | null; target_sell_high?: number | null;
  recommended_quantity?: number | null; capital_required?: number | null; expected_net_profit?: number | null; expected_roi?: number | null;
  expected_holding_seconds?: number | null; expected_profit_per_hour?: number | null; liquidity_score?: number | null;
  acquisition_probability?: number | null; profitable_exit_probability?: number | null; confidence?: number | null; trade_model_confidence?: number | null;
  ea_intervention_risk?: number | null; main_catalyst?: string | null; requires_manual_verification?: boolean; execution_confidence?: number | null; latest_execution_source?: string | null; latest_execution_age_seconds?: number | null;
  invalidation_condition?: string | null; exit_logic?: string | null; score_components?: Record<string, number>;
};

export type VerificationRequest = {
  id: string; candidate_id?: string | null; card_id: string; card: string; card_version: string; rating?: number | null;
  priority: number; reason: string; latest_reference_price?: number | null; reference_timestamp?: string | null;
  reference_age_seconds?: number | null; reference_uncertainty_pct?: number | null; expected_acquisition_range: [number | null, number | null];
  attractive_at_or_below?: number | null; required_information: string; expected_information_value?: number | null;
};
