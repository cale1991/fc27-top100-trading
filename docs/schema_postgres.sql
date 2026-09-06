CREATE TABLE cards (
	id UUID NOT NULL, 
	game_year INTEGER NOT NULL, 
	ea_asset_id BIGINT, 
	ea_resource_id BIGINT, 
	name VARCHAR(160) NOT NULL, 
	rating INTEGER, 
	rarity VARCHAR(96), 
	primary_position VARCHAR(16), 
	league VARCHAR(128), 
	club VARCHAR(128), 
	nation VARCHAR(128), 
	promo VARCHAR(128), 
	image_id VARCHAR(256), 
	image_url TEXT, 
	tradeable BOOLEAN, 
	in_packs BOOLEAN, 
	attributes_json JSONB NOT NULL, 
	playstyles_json JSONB NOT NULL, 
	roles_json JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_card_game_resource UNIQUE (game_year, ea_resource_id)
);

CREATE INDEX ix_cards_club ON cards (club);

CREATE INDEX ix_cards_ea_asset_id ON cards (ea_asset_id);

CREATE INDEX ix_cards_ea_resource_id ON cards (ea_resource_id);

CREATE INDEX ix_cards_game_year ON cards (game_year);

CREATE INDEX ix_cards_in_packs ON cards (in_packs);

CREATE INDEX ix_cards_league ON cards (league);

CREATE INDEX ix_cards_name ON cards (name);

CREATE INDEX ix_cards_nation ON cards (nation);

CREATE INDEX ix_cards_primary_position ON cards (primary_position);

CREATE INDEX ix_cards_promo ON cards (promo);

CREATE INDEX ix_cards_rarity ON cards (rarity);

CREATE INDEX ix_cards_rating ON cards (rating);

CREATE TABLE collector_runs (
	id UUID NOT NULL, 
	collector_key VARCHAR(128) NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(32) NOT NULL, 
	records_seen INTEGER NOT NULL, 
	records_written INTEGER NOT NULL, 
	raw_ingest_count INTEGER NOT NULL, 
	error TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_collector_runs_collector_key ON collector_runs (collector_key);

CREATE INDEX ix_collector_runs_started_at ON collector_runs (started_at);

CREATE INDEX ix_collector_runs_status ON collector_runs (status);

CREATE TABLE community_traders (
	id UUID NOT NULL, 
	source_platform VARCHAR(32) NOT NULL, 
	external_author_id VARCHAR(160), 
	handle VARCHAR(160) NOT NULL, 
	display_name VARCHAR(200), 
	enabled BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_community_trader_handle UNIQUE (source_platform, handle)
);

CREATE INDEX ix_community_traders_created_at ON community_traders (created_at);

CREATE INDEX ix_community_traders_enabled ON community_traders (enabled);

CREATE INDEX ix_community_traders_external_author_id ON community_traders (external_author_id);

CREATE INDEX ix_community_traders_handle ON community_traders (handle);

CREATE INDEX ix_community_traders_source_platform ON community_traders (source_platform);

CREATE TABLE market_segments (
	id UUID NOT NULL, 
	game_year INTEGER NOT NULL, 
	segment_key VARCHAR(64) NOT NULL, 
	display_name VARCHAR(128) NOT NULL, 
	platform VARCHAR(32), 
	platform_group VARCHAR(64), 
	active_from TIMESTAMP WITH TIME ZONE, 
	active_until TIMESTAMP WITH TIME ZONE, 
	executable_by_user BOOLEAN NOT NULL, 
	provider_support_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_market_segment_game_key UNIQUE (game_year, segment_key)
);

CREATE INDEX ix_market_segments_active_from ON market_segments (active_from);

CREATE INDEX ix_market_segments_active_until ON market_segments (active_until);

CREATE INDEX ix_market_segments_executable_by_user ON market_segments (executable_by_user);

CREATE INDEX ix_market_segments_game_year ON market_segments (game_year);

CREATE INDEX ix_market_segments_platform ON market_segments (platform);

CREATE INDEX ix_market_segments_platform_group ON market_segments (platform_group);

CREATE INDEX ix_market_segments_segment_key ON market_segments (segment_key);

CREATE TABLE model_runs (
	id UUID NOT NULL, 
	model_key VARCHAR(128) NOT NULL, 
	model_version VARCHAR(128) NOT NULL, 
	run_started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	run_finished_at TIMESTAMP WITH TIME ZONE, 
	train_start TIMESTAMP WITH TIME ZONE, 
	train_end TIMESTAMP WITH TIME ZONE, 
	validation_start TIMESTAMP WITH TIME ZONE, 
	validation_end TIMESTAMP WITH TIME ZONE, 
	artifact_uri TEXT, 
	config_json JSONB NOT NULL, 
	metrics_json JSONB NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_model_runs_model_key ON model_runs (model_key);

CREATE INDEX ix_model_runs_model_version ON model_runs (model_version);

CREATE INDEX ix_model_runs_run_started_at ON model_runs (run_started_at);

CREATE INDEX ix_model_runs_status ON model_runs (status);

CREATE TABLE persona_state (
	id UUID NOT NULL, 
	account_key VARCHAR(64) NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recent_style_json JSONB NOT NULL, 
	recent_posts_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_persona_state_account_key ON persona_state (account_key);

CREATE INDEX ix_persona_state_updated_at ON persona_state (updated_at);

CREATE TABLE provider_audit_records (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	checked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	tier VARCHAR(16) NOT NULL, 
	integration_status VARCHAR(32) NOT NULL, 
	capabilities_json JSONB NOT NULL, 
	markets_json JSONB NOT NULL, 
	access_json JSONB NOT NULL, 
	rights_json JSONB NOT NULL, 
	economics_json JSONB NOT NULL, 
	source_urls_json JSONB NOT NULL, 
	evidence_notes TEXT, 
	blockers_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_provider_audit_provider_time ON provider_audit_records (provider_key, checked_at);

CREATE INDEX ix_provider_audit_records_checked_at ON provider_audit_records (checked_at);

CREATE INDEX ix_provider_audit_records_integration_status ON provider_audit_records (integration_status);

CREATE INDEX ix_provider_audit_records_provider_key ON provider_audit_records (provider_key);

CREATE INDEX ix_provider_audit_records_tier ON provider_audit_records (tier);

CREATE TABLE provider_budget_states (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	budget_period VARCHAR(32) NOT NULL, 
	access_mode VARCHAR(32) NOT NULL, 
	request_limit BIGINT, 
	requests_used BIGINT NOT NULL, 
	requests_remaining BIGINT, 
	credits_limit NUMERIC(20, 4), 
	credits_used NUMERIC(20, 4) NOT NULL, 
	cost_per_credit NUMERIC(20, 8), 
	estimated_daily_cost NUMERIC(20, 4), 
	estimated_monthly_cost NUMERIC(20, 4), 
	resets_at TIMESTAMP WITH TIME ZONE, 
	priority INTEGER NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_budget_period UNIQUE (provider_key, budget_period)
);

CREATE INDEX ix_provider_budget_states_access_mode ON provider_budget_states (access_mode);

CREATE INDEX ix_provider_budget_states_budget_period ON provider_budget_states (budget_period);

CREATE INDEX ix_provider_budget_states_priority ON provider_budget_states (priority);

CREATE INDEX ix_provider_budget_states_provider_key ON provider_budget_states (provider_key);

CREATE INDEX ix_provider_budget_states_resets_at ON provider_budget_states (resets_at);

CREATE INDEX ix_provider_budget_states_updated_at ON provider_budget_states (updated_at);

CREATE TABLE provider_health (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	provider_role VARCHAR(32) NOT NULL, 
	platform VARCHAR(32) NOT NULL, 
	status VARCHAR(32), 
	access_type VARCHAR(32), 
	enabled BOOLEAN NOT NULL, 
	supported_segments_json JSONB NOT NULL, 
	last_request_at TIMESTAMP WITH TIME ZONE, 
	last_success_at TIMESTAMP WITH TIME ZONE, 
	last_error_at TIMESTAMP WITH TIME ZONE, 
	last_error TEXT, 
	requests_total BIGINT NOT NULL, 
	requests_failed BIGINT NOT NULL, 
	cards_covered INTEGER NOT NULL, 
	latest_observation_at TIMESTAMP WITH TIME ZONE, 
	latest_provider_timestamp TIMESTAMP WITH TIME ZONE, 
	latest_observation_age_seconds NUMERIC(16, 3), 
	last_latency_ms NUMERIC(14, 3), 
	error_rate NUMERIC(10, 8), 
	rate_limit_remaining INTEGER, 
	rate_limit_reset_at TIMESTAMP WITH TIME ZONE, 
	retry_after_seconds INTEGER, 
	items_seen BIGINT NOT NULL, 
	items_ingested BIGINT NOT NULL, 
	duplicates_skipped BIGINT NOT NULL, 
	quarantined_observations BIGINT NOT NULL, 
	parsing_failures BIGINT NOT NULL, 
	normalization_failures BIGINT NOT NULL, 
	identity_failures BIGINT NOT NULL, 
	last_poll_duration_ms NUMERIC(14, 3), 
	gap_status VARCHAR(32), 
	platform_certainty NUMERIC(8, 6), 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_health_role_platform UNIQUE (provider_key, provider_role, platform)
);

CREATE INDEX ix_provider_health_access_type ON provider_health (access_type);

CREATE INDEX ix_provider_health_enabled ON provider_health (enabled);

CREATE INDEX ix_provider_health_gap_status ON provider_health (gap_status);

CREATE INDEX ix_provider_health_last_error_at ON provider_health (last_error_at);

CREATE INDEX ix_provider_health_last_request_at ON provider_health (last_request_at);

CREATE INDEX ix_provider_health_last_success_at ON provider_health (last_success_at);

CREATE INDEX ix_provider_health_latest_observation_at ON provider_health (latest_observation_at);

CREATE INDEX ix_provider_health_latest_provider_timestamp ON provider_health (latest_provider_timestamp);

CREATE INDEX ix_provider_health_platform ON provider_health (platform);

CREATE INDEX ix_provider_health_provider_key ON provider_health (provider_key);

CREATE INDEX ix_provider_health_provider_role ON provider_health (provider_role);

CREATE INDEX ix_provider_health_status ON provider_health (status);

CREATE INDEX ix_provider_health_updated_at ON provider_health (updated_at);

CREATE TABLE provider_qualifications (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	hot_market_eligible BOOLEAN NOT NULL, 
	coverage_pct NUMERIC(8, 4), 
	timestamp_age_p95_seconds NUMERIC(14, 3), 
	propagation_delay_p95_seconds NUMERIC(14, 3), 
	latency_p95_ms NUMERIC(14, 3), 
	median_abs_pct_error NUMERIC(14, 8), 
	rejection_reasons_json JSONB NOT NULL, 
	profile_json JSONB NOT NULL, 
	report_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_provider_qualification_role_time ON provider_qualifications (provider_key, role, evaluated_at);

CREATE INDEX ix_provider_qualifications_evaluated_at ON provider_qualifications (evaluated_at);

CREATE INDEX ix_provider_qualifications_hot_market_eligible ON provider_qualifications (hot_market_eligible);

CREATE INDEX ix_provider_qualifications_platform ON provider_qualifications (platform);

CREATE INDEX ix_provider_qualifications_provider_key ON provider_qualifications (provider_key);

CREATE INDEX ix_provider_qualifications_role ON provider_qualifications (role);

CREATE INDEX ix_provider_qualifications_status ON provider_qualifications (status);

CREATE TABLE provider_validation_runs (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	benchmark_source VARCHAR(64) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	game_year INTEGER NOT NULL, 
	basket_version VARCHAR(64) NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(32) NOT NULL, 
	required_cards INTEGER NOT NULL, 
	paired_cards INTEGER NOT NULL, 
	config_json JSONB NOT NULL, 
	summary_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_provider_validation_runs_benchmark_source ON provider_validation_runs (benchmark_source);

CREATE INDEX ix_provider_validation_runs_completed_at ON provider_validation_runs (completed_at);

CREATE INDEX ix_provider_validation_runs_game_year ON provider_validation_runs (game_year);

CREATE INDEX ix_provider_validation_runs_platform ON provider_validation_runs (platform);

CREATE INDEX ix_provider_validation_runs_provider_key ON provider_validation_runs (provider_key);

CREATE INDEX ix_provider_validation_runs_started_at ON provider_validation_runs (started_at);

CREATE INDEX ix_provider_validation_runs_status ON provider_validation_runs (status);

CREATE TABLE service_heartbeats (
	id UUID NOT NULL, 
	service_key VARCHAR(128) NOT NULL, 
	node_key VARCHAR(128) NOT NULL, 
	service_kind VARCHAR(48) NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_service_heartbeat_node UNIQUE (service_key, node_key)
);

CREATE INDEX ix_service_heartbeats_last_seen_at ON service_heartbeats (last_seen_at);

CREATE INDEX ix_service_heartbeats_node_key ON service_heartbeats (node_key);

CREATE INDEX ix_service_heartbeats_service_key ON service_heartbeats (service_key);

CREATE INDEX ix_service_heartbeats_service_kind ON service_heartbeats (service_kind);

CREATE INDEX ix_service_heartbeats_status ON service_heartbeats (status);

CREATE TABLE shadow_accounts (
	id UUID NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	starting_coins BIGINT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	rules_version VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE sources (
	id UUID NOT NULL, 
	key VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	source_class VARCHAR(32) NOT NULL, 
	automation_policy VARCHAR(64) NOT NULL, 
	training_policy VARCHAR(64) NOT NULL, 
	terms_url TEXT, 
	enabled BOOLEAN NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_sources_key ON sources (key);

CREATE TABLE strategy_library (
	id UUID NOT NULL, 
	slug VARCHAR(160) NOT NULL, 
	canonical_name VARCHAR(200) NOT NULL, 
	explanation TEXT NOT NULL, 
	mechanism TEXT NOT NULL, 
	applicable_card_categories_json JSONB NOT NULL, 
	applicable_market_regimes_json JSONB NOT NULL, 
	catalysts_json JSONB NOT NULL, 
	ideal_entry_conditions_json JSONB NOT NULL, 
	exit_logic TEXT, 
	invalidation_conditions TEXT, 
	typical_capital_requirement_json JSONB NOT NULL, 
	scalability_capacity_json JSONB NOT NULL, 
	expected_holding_period_json JSONB NOT NULL, 
	liquidity_characteristics TEXT, 
	ea_tax_sensitivity VARCHAR(32), 
	ea_intervention_risk VARCHAR(32), 
	first_observed_cycle VARCHAR(32), 
	last_observed_cycle VARCHAR(32), 
	evidence_class VARCHAR(40) NOT NULL, 
	viability_status VARCHAR(48) NOT NULL, 
	measured_status_locked BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_strategy_library_canonical_name ON strategy_library (canonical_name);

CREATE INDEX ix_strategy_library_created_at ON strategy_library (created_at);

CREATE INDEX ix_strategy_library_ea_intervention_risk ON strategy_library (ea_intervention_risk);

CREATE INDEX ix_strategy_library_ea_tax_sensitivity ON strategy_library (ea_tax_sensitivity);

CREATE INDEX ix_strategy_library_evidence_class ON strategy_library (evidence_class);

CREATE INDEX ix_strategy_library_first_observed_cycle ON strategy_library (first_observed_cycle);

CREATE INDEX ix_strategy_library_last_observed_cycle ON strategy_library (last_observed_cycle);

CREATE INDEX ix_strategy_library_measured_status_locked ON strategy_library (measured_status_locked);

CREATE UNIQUE INDEX ix_strategy_library_slug ON strategy_library (slug);

CREATE INDEX ix_strategy_library_updated_at ON strategy_library (updated_at);

CREATE INDEX ix_strategy_library_viability_status ON strategy_library (viability_status);

CREATE TABLE trading_accounts (
	id UUID NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	platform VARCHAR(32) NOT NULL, 
	game_year INTEGER NOT NULL, 
	starting_coins BIGINT NOT NULL, 
	current_coins BIGINT NOT NULL, 
	realized_profit BIGINT NOT NULL, 
	ea_tax_paid BIGINT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_trading_accounts_created_at ON trading_accounts (created_at);

CREATE INDEX ix_trading_accounts_game_year ON trading_accounts (game_year);

CREATE UNIQUE INDEX ix_trading_accounts_name ON trading_accounts (name);

CREATE INDEX ix_trading_accounts_platform ON trading_accounts (platform);

CREATE INDEX ix_trading_accounts_updated_at ON trading_accounts (updated_at);

CREATE TABLE account_constraints (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	game_year INTEGER NOT NULL, 
	transfer_list_capacity INTEGER, 
	unlisted_capacity INTEGER, 
	maximum_desired_exposure BIGINT, 
	per_card_exposure_limit BIGINT, 
	strategy_exposure_json JSONB NOT NULL, 
	market_segment_exposure_json JSONB NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_account_constraint_game UNIQUE (account_id, game_year), 
	FOREIGN KEY(account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE
);

CREATE INDEX ix_account_constraints_account_id ON account_constraints (account_id);

CREATE INDEX ix_account_constraints_game_year ON account_constraints (game_year);

CREATE INDEX ix_account_constraints_updated_at ON account_constraints (updated_at);

CREATE TABLE account_market_access (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	market_segment_id UUID NOT NULL, 
	executable BOOLEAN NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_account_market_access UNIQUE (account_id, market_segment_id), 
	FOREIGN KEY(account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE, 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id) ON DELETE CASCADE
);

CREATE INDEX ix_account_market_access_account_id ON account_market_access (account_id);

CREATE INDEX ix_account_market_access_enabled ON account_market_access (enabled);

CREATE INDEX ix_account_market_access_executable ON account_market_access (executable);

CREATE INDEX ix_account_market_access_market_segment_id ON account_market_access (market_segment_id);

CREATE INDEX ix_account_market_access_updated_at ON account_market_access (updated_at);

CREATE TABLE attention_allocations (
	id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	recomputed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_until TIMESTAMP WITH TIME ZONE NOT NULL, 
	attention_score NUMERIC(16, 8) NOT NULL, 
	tier VARCHAR(32) NOT NULL, 
	target_interval_seconds INTEGER NOT NULL, 
	reasons_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_attention_allocations_attention_score ON attention_allocations (attention_score);

CREATE INDEX ix_attention_allocations_card_id ON attention_allocations (card_id);

CREATE INDEX ix_attention_allocations_platform ON attention_allocations (platform);

CREATE INDEX ix_attention_allocations_recomputed_at ON attention_allocations (recomputed_at);

CREATE INDEX ix_attention_allocations_tier ON attention_allocations (tier);

CREATE INDEX ix_attention_allocations_valid_until ON attention_allocations (valid_until);

CREATE INDEX ix_attention_valid_score ON attention_allocations (valid_until, attention_score);

CREATE TABLE card_relationship_edges (
	id UUID NOT NULL, 
	source_card_id UUID NOT NULL, 
	target_card_id UUID NOT NULL, 
	edge_type VARCHAR(64) NOT NULL, 
	weight NUMERIC(10, 6), 
	valid_from TIMESTAMP WITH TIME ZONE, 
	valid_until TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_card_relationship UNIQUE (source_card_id, target_card_id, edge_type), 
	FOREIGN KEY(source_card_id) REFERENCES cards (id) ON DELETE CASCADE, 
	FOREIGN KEY(target_card_id) REFERENCES cards (id) ON DELETE CASCADE
);

CREATE INDEX ix_card_relationship_edges_edge_type ON card_relationship_edges (edge_type);

CREATE INDEX ix_card_relationship_edges_source_card_id ON card_relationship_edges (source_card_id);

CREATE INDEX ix_card_relationship_edges_target_card_id ON card_relationship_edges (target_card_id);

CREATE INDEX ix_card_relationship_edges_valid_from ON card_relationship_edges (valid_from);

CREATE INDEX ix_card_relationship_edges_valid_until ON card_relationship_edges (valid_until);

CREATE TABLE card_source_ids (
	id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	external_id VARCHAR(160) NOT NULL, 
	source_url TEXT, 
	mapping_method VARCHAR(64), 
	mapping_confidence NUMERIC(8, 6), 
	mapping_status VARCHAR(32), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_card_source_external UNIQUE (source_id, external_id), 
	FOREIGN KEY(card_id) REFERENCES cards (id) ON DELETE CASCADE, 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_card_source_ids_card_id ON card_source_ids (card_id);

CREATE INDEX ix_card_source_ids_mapping_status ON card_source_ids (mapping_status);

CREATE INDEX ix_card_source_ids_source_id ON card_source_ids (source_id);

CREATE TABLE collection_targets (
	id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	tier VARCHAR(32) NOT NULL, 
	target_interval_seconds INTEGER NOT NULL, 
	priority INTEGER NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	last_success_at TIMESTAMP WITH TIME ZONE, 
	next_due_at TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_collection_card_platform UNIQUE (card_id, platform), 
	FOREIGN KEY(card_id) REFERENCES cards (id) ON DELETE CASCADE
);

CREATE INDEX ix_collection_targets_card_id ON collection_targets (card_id);

CREATE INDEX ix_collection_targets_enabled ON collection_targets (enabled);

CREATE INDEX ix_collection_targets_last_success_at ON collection_targets (last_success_at);

CREATE INDEX ix_collection_targets_next_due_at ON collection_targets (next_due_at);

CREATE INDEX ix_collection_targets_platform ON collection_targets (platform);

CREATE INDEX ix_collection_targets_priority ON collection_targets (priority);

CREATE INDEX ix_collection_targets_tier ON collection_targets (tier);

CREATE TABLE data_quality_incidents (
	id UUID NOT NULL, 
	detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_id UUID, 
	severity VARCHAR(16) NOT NULL, 
	incident_type VARCHAR(64) NOT NULL, 
	description TEXT NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_data_quality_incidents_detected_at ON data_quality_incidents (detected_at);

CREATE INDEX ix_data_quality_incidents_incident_type ON data_quality_incidents (incident_type);

CREATE INDEX ix_data_quality_incidents_severity ON data_quality_incidents (severity);

CREATE INDEX ix_data_quality_incidents_source_id ON data_quality_incidents (source_id);

CREATE TABLE derived_feature_snapshots (
	id UUID NOT NULL, 
	feature_family VARCHAR(64) NOT NULL, 
	feature_key VARCHAR(128) NOT NULL, 
	algorithm_version VARCHAR(64) NOT NULL, 
	game_year INTEGER NOT NULL, 
	market_segment_id UUID, 
	card_id UUID, 
	input_cutoff_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	value_json JSONB NOT NULL, 
	source_observation_ids_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_derived_feature_lookup ON derived_feature_snapshots (feature_family, card_id, market_segment_id, input_cutoff_at);

CREATE INDEX ix_derived_feature_snapshots_algorithm_version ON derived_feature_snapshots (algorithm_version);

CREATE INDEX ix_derived_feature_snapshots_calculated_at ON derived_feature_snapshots (calculated_at);

CREATE INDEX ix_derived_feature_snapshots_card_id ON derived_feature_snapshots (card_id);

CREATE INDEX ix_derived_feature_snapshots_feature_family ON derived_feature_snapshots (feature_family);

CREATE INDEX ix_derived_feature_snapshots_feature_key ON derived_feature_snapshots (feature_key);

CREATE INDEX ix_derived_feature_snapshots_game_year ON derived_feature_snapshots (game_year);

CREATE INDEX ix_derived_feature_snapshots_input_cutoff_at ON derived_feature_snapshots (input_cutoff_at);

CREATE INDEX ix_derived_feature_snapshots_market_segment_id ON derived_feature_snapshots (market_segment_id);

CREATE TABLE evolutions (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	external_id VARCHAR(160), 
	game_year INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	coin_cost INTEGER, 
	fc_point_cost INTEGER, 
	starts_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	upgrades_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_evolutions_expires_at ON evolutions (expires_at);

CREATE INDEX ix_evolutions_external_id ON evolutions (external_id);

CREATE INDEX ix_evolutions_game_year ON evolutions (game_year);

CREATE INDEX ix_evolutions_name ON evolutions (name);

CREATE INDEX ix_evolutions_source_id ON evolutions (source_id);

CREATE TABLE historical_import_batches (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	source_format VARCHAR(32) NOT NULL, 
	source_uri TEXT, 
	imported_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	game_year INTEGER NOT NULL, 
	market_segment_id UUID, 
	native_historical BOOLEAN NOT NULL, 
	reconstructed BOOLEAN NOT NULL, 
	rows_seen BIGINT NOT NULL, 
	rows_written BIGINT NOT NULL, 
	rows_quarantined BIGINT NOT NULL, 
	checksum_sha256 VARCHAR(64), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id)
);

CREATE INDEX ix_historical_import_batches_checksum_sha256 ON historical_import_batches (checksum_sha256);

CREATE INDEX ix_historical_import_batches_game_year ON historical_import_batches (game_year);

CREATE INDEX ix_historical_import_batches_imported_at ON historical_import_batches (imported_at);

CREATE INDEX ix_historical_import_batches_market_segment_id ON historical_import_batches (market_segment_id);

CREATE INDEX ix_historical_import_batches_provider_key ON historical_import_batches (provider_key);

CREATE INDEX ix_historical_import_batches_source_format ON historical_import_batches (source_format);

CREATE TABLE market_index_snapshots (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	index_key VARCHAR(128) NOT NULL, 
	value NUMERIC(20, 6) NOT NULL, 
	constituent_count INTEGER, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_market_index_snapshots_index_key ON market_index_snapshots (index_key);

CREATE INDEX ix_market_index_snapshots_observed_at ON market_index_snapshots (observed_at);

CREATE INDEX ix_market_index_snapshots_platform ON market_index_snapshots (platform);

CREATE INDEX ix_market_index_snapshots_source_id ON market_index_snapshots (source_id);

CREATE TABLE packs (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	external_id VARCHAR(160), 
	game_year INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	coin_price INTEGER, 
	fc_point_price INTEGER, 
	available_from TIMESTAMP WITH TIME ZONE, 
	available_until TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_packs_available_until ON packs (available_until);

CREATE INDEX ix_packs_external_id ON packs (external_id);

CREATE INDEX ix_packs_game_year ON packs (game_year);

CREATE INDEX ix_packs_name ON packs (name);

CREATE INDEX ix_packs_source_id ON packs (source_id);

CREATE TABLE portfolio_positions (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	market_segment_id UUID, 
	quantity INTEGER NOT NULL, 
	average_acquisition_price INTEGER NOT NULL, 
	total_cost_basis BIGINT NOT NULL, 
	desired_listing_price INTEGER, 
	opened_at TIMESTAMP WITH TIME ZONE, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	current_action VARCHAR(32), 
	urgency INTEGER NOT NULL, 
	original_thesis TEXT, 
	original_catalyst TEXT, 
	thesis_status VARCHAR(64), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_portfolio_account_card_segment UNIQUE (account_id, card_id, market_segment_id), 
	FOREIGN KEY(account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE, 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id)
);

CREATE INDEX ix_portfolio_open_urgency ON portfolio_positions (account_id, status, urgency);

CREATE INDEX ix_portfolio_positions_account_id ON portfolio_positions (account_id);

CREATE INDEX ix_portfolio_positions_card_id ON portfolio_positions (card_id);

CREATE INDEX ix_portfolio_positions_current_action ON portfolio_positions (current_action);

CREATE INDEX ix_portfolio_positions_market_segment_id ON portfolio_positions (market_segment_id);

CREATE INDEX ix_portfolio_positions_opened_at ON portfolio_positions (opened_at);

CREATE INDEX ix_portfolio_positions_status ON portfolio_positions (status);

CREATE INDEX ix_portfolio_positions_thesis_status ON portfolio_positions (thesis_status);

CREATE INDEX ix_portfolio_positions_updated_at ON portfolio_positions (updated_at);

CREATE INDEX ix_portfolio_positions_urgency ON portfolio_positions (urgency);

CREATE TABLE portfolio_snapshots (
	id BIGSERIAL NOT NULL, 
	account_id UUID NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	available_coins BIGINT NOT NULL, 
	invested_coins BIGINT NOT NULL, 
	unrealized_profit BIGINT NOT NULL, 
	realized_profit BIGINT NOT NULL, 
	ea_tax_paid BIGINT NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES shadow_accounts (id)
);

CREATE INDEX ix_portfolio_snapshots_account_id ON portfolio_snapshots (account_id);

CREATE INDEX ix_portfolio_snapshots_observed_at ON portfolio_snapshots (observed_at);

CREATE TABLE predictions (
	id UUID NOT NULL, 
	generated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	card_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	model_key VARCHAR(128) NOT NULL, 
	model_version VARCHAR(128) NOT NULL, 
	horizon_seconds INTEGER NOT NULL, 
	current_price INTEGER, 
	future_sell_price INTEGER, 
	profitable_exit_probability NUMERIC(8, 6), 
	expected_net_profit INTEGER, 
	expected_time_to_sale_seconds INTEGER, 
	expected_profit_per_hour NUMERIC(20, 6), 
	expected_profit_per_capital NUMERIC(12, 8), 
	max_position_size INTEGER, 
	downside_risk NUMERIC(12, 8), 
	catalyst_failure_probability NUMERIC(8, 6), 
	payload_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_predictions_card_id ON predictions (card_id);

CREATE INDEX ix_predictions_generated_at ON predictions (generated_at);

CREATE INDEX ix_predictions_horizon_seconds ON predictions (horizon_seconds);

CREATE INDEX ix_predictions_model_key ON predictions (model_key);

CREATE INDEX ix_predictions_model_version ON predictions (model_version);

CREATE INDEX ix_predictions_platform ON predictions (platform);

CREATE TABLE provider_entities (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	entity_type VARCHAR(32) NOT NULL, 
	external_id VARCHAR(160) NOT NULL, 
	name VARCHAR(160), 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_entity UNIQUE (source_id, entity_type, external_id), 
	FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE CASCADE
);

CREATE INDEX ix_provider_entities_entity_type ON provider_entities (entity_type);

CREATE INDEX ix_provider_entities_name ON provider_entities (name);

CREATE INDEX ix_provider_entities_source_id ON provider_entities (source_id);

CREATE INDEX ix_provider_entities_updated_at ON provider_entities (updated_at);

CREATE TABLE provider_feed_states (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	feed_key VARCHAR(64) NOT NULL, 
	source_url TEXT NOT NULL, 
	etag VARCHAR(256), 
	last_modified VARCHAR(256), 
	last_poll_at TIMESTAMP WITH TIME ZONE, 
	last_success_at TIMESTAMP WITH TIME ZONE, 
	last_http_status INTEGER, 
	consecutive_failures INTEGER NOT NULL, 
	newest_provider_event_at TIMESTAMP WITH TIME ZONE, 
	oldest_provider_event_at TIMESTAMP WITH TIME ZONE, 
	inferred_coverage_seconds INTEGER, 
	gap_status VARCHAR(32) NOT NULL, 
	next_allowed_at TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_feed_state UNIQUE (source_id, feed_key), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_provider_feed_states_feed_key ON provider_feed_states (feed_key);

CREATE INDEX ix_provider_feed_states_gap_status ON provider_feed_states (gap_status);

CREATE INDEX ix_provider_feed_states_last_poll_at ON provider_feed_states (last_poll_at);

CREATE INDEX ix_provider_feed_states_last_success_at ON provider_feed_states (last_success_at);

CREATE INDEX ix_provider_feed_states_newest_provider_event_at ON provider_feed_states (newest_provider_event_at);

CREATE INDEX ix_provider_feed_states_next_allowed_at ON provider_feed_states (next_allowed_at);

CREATE INDEX ix_provider_feed_states_oldest_provider_event_at ON provider_feed_states (oldest_provider_event_at);

CREATE INDEX ix_provider_feed_states_source_id ON provider_feed_states (source_id);

CREATE TABLE provider_reliability_snapshots (
	id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	market_segment_id UUID, 
	card_id UUID, 
	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	sample_size INTEGER NOT NULL, 
	dimensions_json JSONB NOT NULL, 
	metrics_json JSONB NOT NULL, 
	confidence NUMERIC(8, 6), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_provider_reliability_snapshots_calculated_at ON provider_reliability_snapshots (calculated_at);

CREATE INDEX ix_provider_reliability_snapshots_card_id ON provider_reliability_snapshots (card_id);

CREATE INDEX ix_provider_reliability_snapshots_market_segment_id ON provider_reliability_snapshots (market_segment_id);

CREATE INDEX ix_provider_reliability_snapshots_provider_key ON provider_reliability_snapshots (provider_key);

CREATE TABLE provider_validation_observations (
	id BIGSERIAL NOT NULL, 
	run_id UUID NOT NULL, 
	provider_key VARCHAR(64) NOT NULL, 
	card_key VARCHAR(160) NOT NULL, 
	category VARCHAR(32) NOT NULL, 
	provider_price_pc INTEGER, 
	benchmark_price_pc INTEGER NOT NULL, 
	provider_timestamp TIMESTAMP WITH TIME ZONE, 
	provider_observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	benchmark_observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	http_latency_ms NUMERIC(12, 3), 
	provider_age_seconds NUMERIC(14, 3), 
	observed_skew_seconds NUMERIC(14, 3) NOT NULL, 
	absolute_error_coins INTEGER, 
	absolute_pct_error NUMERIC(14, 8), 
	raw_reference TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_validation_run_card UNIQUE (run_id, card_key), 
	FOREIGN KEY(run_id) REFERENCES provider_validation_runs (id) ON DELETE CASCADE
);

CREATE INDEX ix_provider_validation_observations_benchmark_observed_at ON provider_validation_observations (benchmark_observed_at);

CREATE INDEX ix_provider_validation_observations_card_key ON provider_validation_observations (card_key);

CREATE INDEX ix_provider_validation_observations_category ON provider_validation_observations (category);

CREATE INDEX ix_provider_validation_observations_provider_key ON provider_validation_observations (provider_key);

CREATE INDEX ix_provider_validation_observations_provider_observed_at ON provider_validation_observations (provider_observed_at);

CREATE INDEX ix_provider_validation_observations_provider_timestamp ON provider_validation_observations (provider_timestamp);

CREATE INDEX ix_provider_validation_observations_run_id ON provider_validation_observations (run_id);

CREATE TABLE public_predictions (
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE, 
	card_id UUID, 
	category_key VARCHAR(128), 
	full_post TEXT NOT NULL, 
	market_state_json JSONB NOT NULL, 
	prediction TEXT NOT NULL, 
	target_price INTEGER, 
	horizon_seconds INTEGER, 
	confidence NUMERIC(8, 6), 
	catalyst TEXT, 
	status VARCHAR(32) NOT NULL, 
	result_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_public_predictions_card_id ON public_predictions (card_id);

CREATE INDEX ix_public_predictions_category_key ON public_predictions (category_key);

CREATE INDEX ix_public_predictions_created_at ON public_predictions (created_at);

CREATE INDEX ix_public_predictions_horizon_seconds ON public_predictions (horizon_seconds);

CREATE INDEX ix_public_predictions_published_at ON public_predictions (published_at);

CREATE INDEX ix_public_predictions_status ON public_predictions (status);

CREATE TABLE raw_ingests (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	source_kind VARCHAR(64) NOT NULL, 
	request_url TEXT NOT NULL, 
	request_method VARCHAR(16) NOT NULL, 
	http_status INTEGER, 
	content_type VARCHAR(128), 
	source_timestamp TIMESTAMP WITH TIME ZONE, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	checksum_sha256 VARCHAR(64) NOT NULL, 
	etag VARCHAR(256), 
	last_modified VARCHAR(256), 
	storage_uri TEXT NOT NULL, 
	payload_size BIGINT NOT NULL, 
	parser_version VARCHAR(64), 
	schema_version VARCHAR(64), 
	inserted_at TIMESTAMP WITH TIME ZONE, 
	success BOOLEAN NOT NULL, 
	error TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_raw_source_checksum UNIQUE (source_id, checksum_sha256), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_raw_ingests_checksum_sha256 ON raw_ingests (checksum_sha256);

CREATE INDEX ix_raw_ingests_inserted_at ON raw_ingests (inserted_at);

CREATE INDEX ix_raw_ingests_observed_at ON raw_ingests (observed_at);

CREATE INDEX ix_raw_ingests_retrieved_at ON raw_ingests (retrieved_at);

CREATE INDEX ix_raw_ingests_source_id ON raw_ingests (source_id);

CREATE INDEX ix_raw_ingests_source_kind ON raw_ingests (source_kind);

CREATE TABLE sbcs (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	external_id VARCHAR(160), 
	game_year INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	category VARCHAR(64), 
	repeatable_count INTEGER, 
	refresh_seconds INTEGER, 
	starts_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	reward_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id)
);

CREATE INDEX ix_sbcs_category ON sbcs (category);

CREATE INDEX ix_sbcs_expires_at ON sbcs (expires_at);

CREATE INDEX ix_sbcs_external_id ON sbcs (external_id);

CREATE INDEX ix_sbcs_game_year ON sbcs (game_year);

CREATE INDEX ix_sbcs_name ON sbcs (name);

CREATE INDEX ix_sbcs_source_id ON sbcs (source_id);

CREATE TABLE shadow_trades (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	opened_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITH TIME ZONE, 
	quantity INTEGER NOT NULL, 
	average_buy_price INTEGER NOT NULL, 
	average_sell_price INTEGER, 
	ea_tax_paid INTEGER NOT NULL, 
	predicted_profit INTEGER, 
	realized_profit INTEGER, 
	holding_seconds INTEGER, 
	model_confidence NUMERIC(8, 6), 
	strategy_key VARCHAR(128), 
	entry_reason TEXT, 
	exit_reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES shadow_accounts (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_shadow_trades_account_id ON shadow_trades (account_id);

CREATE INDEX ix_shadow_trades_card_id ON shadow_trades (card_id);

CREATE INDEX ix_shadow_trades_closed_at ON shadow_trades (closed_at);

CREATE INDEX ix_shadow_trades_opened_at ON shadow_trades (opened_at);

CREATE INDEX ix_shadow_trades_strategy_key ON shadow_trades (strategy_key);

CREATE TABLE strategy_aliases (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	alias VARCHAR(200) NOT NULL, 
	terminology_source VARCHAR(128), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_strategy_alias UNIQUE (strategy_id, alias), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE
);

CREATE INDEX ix_strategy_aliases_alias ON strategy_aliases (alias);

CREATE INDEX ix_strategy_aliases_strategy_id ON strategy_aliases (strategy_id);

CREATE TABLE strategy_backtest_runs (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	game_cycle VARCHAR(32) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	dataset_start TIMESTAMP WITH TIME ZONE, 
	dataset_end TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(32) NOT NULL, 
	sample_size INTEGER NOT NULL, 
	acquisition_attempt_sample_size INTEGER NOT NULL, 
	code_version VARCHAR(128), 
	config_json JSONB NOT NULL, 
	metrics_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE
);

CREATE INDEX ix_strategy_backtest_runs_finished_at ON strategy_backtest_runs (finished_at);

CREATE INDEX ix_strategy_backtest_runs_game_cycle ON strategy_backtest_runs (game_cycle);

CREATE INDEX ix_strategy_backtest_runs_platform ON strategy_backtest_runs (platform);

CREATE INDEX ix_strategy_backtest_runs_started_at ON strategy_backtest_runs (started_at);

CREATE INDEX ix_strategy_backtest_runs_status ON strategy_backtest_runs (status);

CREATE INDEX ix_strategy_backtest_runs_strategy_id ON strategy_backtest_runs (strategy_id);

CREATE TABLE strategy_cycle_assessments (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	game_cycle VARCHAR(32) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	assessed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	evidence_weight NUMERIC(8, 6), 
	structural_difference_score NUMERIC(8, 6), 
	decay_risk NUMERIC(8, 6), 
	viability_status VARCHAR(48) NOT NULL, 
	reason TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_strategy_cycle_platform UNIQUE (strategy_id, game_cycle, platform), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE
);

CREATE INDEX ix_strategy_cycle_assessments_assessed_at ON strategy_cycle_assessments (assessed_at);

CREATE INDEX ix_strategy_cycle_assessments_decay_risk ON strategy_cycle_assessments (decay_risk);

CREATE INDEX ix_strategy_cycle_assessments_game_cycle ON strategy_cycle_assessments (game_cycle);

CREATE INDEX ix_strategy_cycle_assessments_platform ON strategy_cycle_assessments (platform);

CREATE INDEX ix_strategy_cycle_assessments_strategy_id ON strategy_cycle_assessments (strategy_id);

CREATE INDEX ix_strategy_cycle_assessments_viability_status ON strategy_cycle_assessments (viability_status);

CREATE TABLE strategy_discovery_candidates (
	id UUID NOT NULL, 
	pattern_key VARCHAR(200) NOT NULL, 
	first_detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	sample_size INTEGER NOT NULL, 
	effect_size NUMERIC(14, 8), 
	confidence NUMERIC(8, 6), 
	description TEXT, 
	feature_signature_json JSONB NOT NULL, 
	supporting_outcomes_json JSONB NOT NULL, 
	review_notes TEXT, 
	promoted_strategy_id UUID, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(promoted_strategy_id) REFERENCES strategy_library (id)
);

CREATE INDEX ix_strategy_discovery_candidates_confidence ON strategy_discovery_candidates (confidence);

CREATE INDEX ix_strategy_discovery_candidates_first_detected_at ON strategy_discovery_candidates (first_detected_at);

CREATE INDEX ix_strategy_discovery_candidates_last_seen_at ON strategy_discovery_candidates (last_seen_at);

CREATE UNIQUE INDEX ix_strategy_discovery_candidates_pattern_key ON strategy_discovery_candidates (pattern_key);

CREATE INDEX ix_strategy_discovery_candidates_promoted_strategy_id ON strategy_discovery_candidates (promoted_strategy_id);

CREATE INDEX ix_strategy_discovery_candidates_status ON strategy_discovery_candidates (status);

CREATE TABLE strategy_evidence (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	game_cycle VARCHAR(32) NOT NULL, 
	source_kind VARCHAR(64) NOT NULL, 
	source_title TEXT, 
	source_url TEXT NOT NULL, 
	author VARCHAR(200), 
	published_at TIMESTAMP WITH TIME ZONE, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	evidence_type VARCHAR(80) NOT NULL, 
	evidence_direction VARCHAR(32) NOT NULL, 
	quality_score NUMERIC(8, 6), 
	trader_id UUID, 
	notes TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE, 
	FOREIGN KEY(trader_id) REFERENCES community_traders (id)
);

CREATE INDEX ix_strategy_evidence_author ON strategy_evidence (author);

CREATE INDEX ix_strategy_evidence_evidence_direction ON strategy_evidence (evidence_direction);

CREATE INDEX ix_strategy_evidence_evidence_type ON strategy_evidence (evidence_type);

CREATE INDEX ix_strategy_evidence_game_cycle ON strategy_evidence (game_cycle);

CREATE INDEX ix_strategy_evidence_published_at ON strategy_evidence (published_at);

CREATE INDEX ix_strategy_evidence_recorded_at ON strategy_evidence (recorded_at);

CREATE INDEX ix_strategy_evidence_source_kind ON strategy_evidence (source_kind);

CREATE INDEX ix_strategy_evidence_strategy_cycle ON strategy_evidence (strategy_id, game_cycle, published_at);

CREATE INDEX ix_strategy_evidence_strategy_id ON strategy_evidence (strategy_id);

CREATE INDEX ix_strategy_evidence_trader_id ON strategy_evidence (trader_id);

CREATE TABLE strategy_trader_performance (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	trader_id UUID NOT NULL, 
	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	sample_size INTEGER NOT NULL, 
	directional_accuracy NUMERIC(8, 6), 
	profitable_after_tax_rate NUMERIC(8, 6), 
	average_return_pct NUMERIC(14, 8), 
	median_return_pct NUMERIC(14, 8), 
	average_alpha_pct NUMERIC(14, 8), 
	max_drawdown_pct NUMERIC(14, 8), 
	timing_quality NUMERIC(8, 6), 
	average_holding_seconds INTEGER, 
	recent_form_score NUMERIC(8, 6), 
	sample_confidence NUMERIC(8, 6), 
	reputation_score NUMERIC(8, 6), 
	category_metrics_json JSONB NOT NULL, 
	horizon_metrics_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE, 
	FOREIGN KEY(trader_id) REFERENCES community_traders (id) ON DELETE CASCADE
);

CREATE INDEX ix_strategy_trader_performance_calculated_at ON strategy_trader_performance (calculated_at);

CREATE INDEX ix_strategy_trader_performance_reputation_score ON strategy_trader_performance (reputation_score);

CREATE INDEX ix_strategy_trader_performance_strategy_id ON strategy_trader_performance (strategy_id);

CREATE INDEX ix_strategy_trader_performance_trader_id ON strategy_trader_performance (trader_id);

CREATE INDEX ix_strategy_trader_strategy_trader_time ON strategy_trader_performance (strategy_id, trader_id, calculated_at);

CREATE TABLE trader_reputation_snapshots (
	id UUID NOT NULL, 
	trader_id UUID NOT NULL, 
	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	sample_size INTEGER NOT NULL, 
	directional_accuracy NUMERIC(8, 6), 
	profitable_after_tax_rate NUMERIC(8, 6), 
	average_return_pct NUMERIC(14, 8), 
	median_return_pct NUMERIC(14, 8), 
	average_alpha_pct NUMERIC(14, 8), 
	max_drawdown_pct NUMERIC(14, 8), 
	average_drawdown_pct NUMERIC(14, 8), 
	timing_quality NUMERIC(8, 6), 
	average_holding_seconds INTEGER, 
	recent_form_score NUMERIC(8, 6), 
	sample_confidence NUMERIC(8, 6), 
	reputation_score NUMERIC(8, 6), 
	category_metrics_json JSONB NOT NULL, 
	horizon_metrics_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(trader_id) REFERENCES community_traders (id) ON DELETE CASCADE
);

CREATE INDEX ix_trader_reputation_snapshots_calculated_at ON trader_reputation_snapshots (calculated_at);

CREATE INDEX ix_trader_reputation_snapshots_reputation_score ON trader_reputation_snapshots (reputation_score);

CREATE INDEX ix_trader_reputation_snapshots_trader_id ON trader_reputation_snapshots (trader_id);

CREATE TABLE community_content (
	id UUID NOT NULL, 
	trader_id UUID, 
	source_id UUID, 
	external_id VARCHAR(200), 
	published_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_url TEXT, 
	text TEXT NOT NULL, 
	raw_ingest_id UUID, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(trader_id) REFERENCES community_traders (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_community_content_external_id ON community_content (external_id);

CREATE INDEX ix_community_content_observed_at ON community_content (observed_at);

CREATE INDEX ix_community_content_published_at ON community_content (published_at);

CREATE INDEX ix_community_content_source_id ON community_content (source_id);

CREATE INDEX ix_community_content_trader_id ON community_content (trader_id);

CREATE TABLE completed_sale_observations (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	sold_at TIMESTAMP WITH TIME ZONE, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	price INTEGER NOT NULL, 
	external_trade_id VARCHAR(128), 
	raw_ingest_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_completed_sale_observations_card_id ON completed_sale_observations (card_id);

CREATE INDEX ix_completed_sale_observations_external_trade_id ON completed_sale_observations (external_trade_id);

CREATE INDEX ix_completed_sale_observations_observed_at ON completed_sale_observations (observed_at);

CREATE INDEX ix_completed_sale_observations_platform ON completed_sale_observations (platform);

CREATE INDEX ix_completed_sale_observations_sold_at ON completed_sale_observations (sold_at);

CREATE INDEX ix_completed_sale_observations_source_id ON completed_sale_observations (source_id);

CREATE TABLE content_events (
	id UUID NOT NULL, 
	event_hash VARCHAR(64) NOT NULL, 
	game_year INTEGER NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	evidence_class VARCHAR(32) NOT NULL, 
	source_id UUID NOT NULL, 
	raw_ingest_id UUID, 
	external_id VARCHAR(160), 
	title TEXT NOT NULL, 
	summary TEXT, 
	published_at TIMESTAMP WITH TIME ZONE, 
	effective_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_url TEXT, 
	payload_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_content_events_detected_at ON content_events (detected_at);

CREATE INDEX ix_content_events_effective_at ON content_events (effective_at);

CREATE UNIQUE INDEX ix_content_events_event_hash ON content_events (event_hash);

CREATE INDEX ix_content_events_event_type ON content_events (event_type);

CREATE INDEX ix_content_events_evidence_class ON content_events (evidence_class);

CREATE INDEX ix_content_events_expires_at ON content_events (expires_at);

CREATE INDEX ix_content_events_external_id ON content_events (external_id);

CREATE INDEX ix_content_events_game_year ON content_events (game_year);

CREATE INDEX ix_content_events_published_at ON content_events (published_at);

CREATE INDEX ix_content_events_source_id ON content_events (source_id);

CREATE TABLE evolution_requirements (
	id UUID NOT NULL, 
	evolution_id UUID NOT NULL, 
	requirement_type VARCHAR(64) NOT NULL, 
	operator VARCHAR(16), 
	value_numeric NUMERIC(12, 4), 
	value_text VARCHAR(160), 
	payload_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(evolution_id) REFERENCES evolutions (id) ON DELETE CASCADE
);

CREATE INDEX ix_evolution_requirements_evolution_id ON evolution_requirements (evolution_id);

CREATE INDEX ix_evolution_requirements_requirement_type ON evolution_requirements (requirement_type);

CREATE INDEX ix_evolution_requirements_value_text ON evolution_requirements (value_text);

CREATE TABLE execution_observations (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_timestamp TIMESTAMP WITH TIME ZONE, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	raw_ingest_id UUID, 
	market_segment_id UUID, 
	platform VARCHAR(32) NOT NULL, 
	inserted_at TIMESTAMP WITH TIME ZONE, 
	observation_type VARCHAR(64) NOT NULL, 
	lowest_bin INTEGER, 
	best_bid INTEGER, 
	listing_prices_json JSONB NOT NULL, 
	listing_count INTEGER, 
	confidence NUMERIC(8, 6) NOT NULL, 
	quality_status VARCHAR(32) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	manual_verification_request_id UUID, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id)
);

CREATE INDEX ix_execution_card_platform_time ON execution_observations (card_id, platform, observed_at);

CREATE INDEX ix_execution_observations_card_id ON execution_observations (card_id);

CREATE INDEX ix_execution_observations_expires_at ON execution_observations (expires_at);

CREATE INDEX ix_execution_observations_inserted_at ON execution_observations (inserted_at);

CREATE INDEX ix_execution_observations_manual_verification_request_id ON execution_observations (manual_verification_request_id);

CREATE INDEX ix_execution_observations_market_segment_id ON execution_observations (market_segment_id);

CREATE INDEX ix_execution_observations_observation_type ON execution_observations (observation_type);

CREATE INDEX ix_execution_observations_observed_at ON execution_observations (observed_at);

CREATE INDEX ix_execution_observations_platform ON execution_observations (platform);

CREATE INDEX ix_execution_observations_quality_status ON execution_observations (quality_status);

CREATE INDEX ix_execution_observations_source_id ON execution_observations (source_id);

CREATE INDEX ix_execution_observations_source_timestamp ON execution_observations (source_timestamp);

CREATE TABLE market_listing_observations (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	external_trade_id VARCHAR(128), 
	current_bid INTEGER, 
	buy_now INTEGER, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	raw_ingest_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_market_listing_observations_card_id ON market_listing_observations (card_id);

CREATE INDEX ix_market_listing_observations_external_trade_id ON market_listing_observations (external_trade_id);

CREATE INDEX ix_market_listing_observations_observed_at ON market_listing_observations (observed_at);

CREATE INDEX ix_market_listing_observations_platform ON market_listing_observations (platform);

CREATE INDEX ix_market_listing_observations_source_id ON market_listing_observations (source_id);

CREATE TABLE market_snapshots (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	source_timestamp TIMESTAMP WITH TIME ZONE, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	raw_ingest_id UUID, 
	platform VARCHAR(16) NOT NULL, 
	lowest_bin INTEGER, 
	best_bid INTEGER, 
	active_listings INTEGER, 
	sales_5m INTEGER, 
	sales_15m INTEGER, 
	spread_abs INTEGER, 
	spread_pct NUMERIC(12, 6), 
	price_min INTEGER, 
	price_max INTEGER, 
	source_updated_at TIMESTAMP WITH TIME ZONE, 
	quality_score NUMERIC(5, 4), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_market_card_platform_time ON market_snapshots (card_id, platform, observed_at);

CREATE INDEX ix_market_snapshots_card_id ON market_snapshots (card_id);

CREATE INDEX ix_market_snapshots_observed_at ON market_snapshots (observed_at);

CREATE INDEX ix_market_snapshots_platform ON market_snapshots (platform);

CREATE INDEX ix_market_snapshots_source_id ON market_snapshots (source_id);

CREATE INDEX ix_market_snapshots_source_timestamp ON market_snapshots (source_timestamp);

CREATE TABLE pack_probabilities (
	id UUID NOT NULL, 
	pack_id UUID NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	category VARCHAR(160) NOT NULL, 
	minimum_probability NUMERIC(8, 6) NOT NULL, 
	raw_ingest_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pack_id) REFERENCES packs (id) ON DELETE CASCADE, 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id)
);

CREATE INDEX ix_pack_probabilities_category ON pack_probabilities (category);

CREATE INDEX ix_pack_probabilities_observed_at ON pack_probabilities (observed_at);

CREATE INDEX ix_pack_probabilities_pack_id ON pack_probabilities (pack_id);

CREATE TABLE portfolio_transactions (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	position_id UUID, 
	market_segment_id UUID, 
	card_id UUID, 
	transaction_type VARCHAR(32) NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price INTEGER, 
	gross_amount BIGINT NOT NULL, 
	ea_tax BIGINT NOT NULL, 
	net_coin_flow BIGINT NOT NULL, 
	cost_basis_released BIGINT NOT NULL, 
	realized_profit BIGINT NOT NULL, 
	notes TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES trading_accounts (id) ON DELETE CASCADE, 
	FOREIGN KEY(position_id) REFERENCES portfolio_positions (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_portfolio_transactions_account_id ON portfolio_transactions (account_id);

CREATE INDEX ix_portfolio_transactions_card_id ON portfolio_transactions (card_id);

CREATE INDEX ix_portfolio_transactions_market_segment_id ON portfolio_transactions (market_segment_id);

CREATE INDEX ix_portfolio_transactions_occurred_at ON portfolio_transactions (occurred_at);

CREATE INDEX ix_portfolio_transactions_position_id ON portfolio_transactions (position_id);

CREATE INDEX ix_portfolio_transactions_transaction_type ON portfolio_transactions (transaction_type);

CREATE TABLE provider_feed_events (
	id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	raw_ingest_id UUID, 
	market_segment_id UUID, 
	game_year INTEGER NOT NULL, 
	feed_key VARCHAR(64) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	provider_event_id VARCHAR(256) NOT NULL, 
	provider_card_id VARCHAR(160), 
	card_id UUID, 
	identity_status VARCHAR(32) NOT NULL, 
	title TEXT NOT NULL, 
	description TEXT, 
	source_url TEXT, 
	entity_url TEXT, 
	provider_timestamp TIMESTAMP WITH TIME ZONE, 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	inserted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	old_price INTEGER, 
	new_price INTEGER, 
	absolute_change INTEGER, 
	percentage_change NUMERIC(14, 8), 
	rating INTEGER, 
	card_version VARCHAR(128), 
	observation_semantics VARCHAR(32) NOT NULL, 
	state_completeness VARCHAR(32) NOT NULL, 
	quality_status VARCHAR(32) NOT NULL, 
	parser_version VARCHAR(64), 
	payload_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_feed_event_identity UNIQUE (source_id, feed_key, provider_event_id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_provider_feed_card_time ON provider_feed_events (card_id, provider_timestamp);

CREATE INDEX ix_provider_feed_events_card_id ON provider_feed_events (card_id);

CREATE INDEX ix_provider_feed_events_card_version ON provider_feed_events (card_version);

CREATE INDEX ix_provider_feed_events_event_type ON provider_feed_events (event_type);

CREATE INDEX ix_provider_feed_events_feed_key ON provider_feed_events (feed_key);

CREATE INDEX ix_provider_feed_events_game_year ON provider_feed_events (game_year);

CREATE INDEX ix_provider_feed_events_identity_status ON provider_feed_events (identity_status);

CREATE INDEX ix_provider_feed_events_inserted_at ON provider_feed_events (inserted_at);

CREATE INDEX ix_provider_feed_events_market_segment_id ON provider_feed_events (market_segment_id);

CREATE INDEX ix_provider_feed_events_observation_semantics ON provider_feed_events (observation_semantics);

CREATE INDEX ix_provider_feed_events_provider_card_id ON provider_feed_events (provider_card_id);

CREATE INDEX ix_provider_feed_events_provider_timestamp ON provider_feed_events (provider_timestamp);

CREATE INDEX ix_provider_feed_events_quality_status ON provider_feed_events (quality_status);

CREATE INDEX ix_provider_feed_events_rating ON provider_feed_events (rating);

CREATE INDEX ix_provider_feed_events_raw_ingest_id ON provider_feed_events (raw_ingest_id);

CREATE INDEX ix_provider_feed_events_retrieved_at ON provider_feed_events (retrieved_at);

CREATE INDEX ix_provider_feed_events_source_id ON provider_feed_events (source_id);

CREATE INDEX ix_provider_feed_events_state_completeness ON provider_feed_events (state_completeness);

CREATE TABLE public_posts (
	id UUID NOT NULL, 
	prediction_id UUID, 
	platform VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE, 
	external_post_id VARCHAR(200), 
	text TEXT NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	preflight_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(prediction_id) REFERENCES public_predictions (id)
);

CREATE INDEX ix_public_posts_created_at ON public_posts (created_at);

CREATE INDEX ix_public_posts_external_post_id ON public_posts (external_post_id);

CREATE INDEX ix_public_posts_platform ON public_posts (platform);

CREATE INDEX ix_public_posts_prediction_id ON public_posts (prediction_id);

CREATE INDEX ix_public_posts_published_at ON public_posts (published_at);

CREATE INDEX ix_public_posts_status ON public_posts (status);

CREATE TABLE reference_price_observations (
	id BIGSERIAL NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	provider_timestamp TIMESTAMP WITH TIME ZONE, 
	card_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	raw_ingest_id UUID, 
	market_segment_id UUID, 
	platform VARCHAR(32) NOT NULL, 
	inserted_at TIMESTAMP WITH TIME ZONE, 
	price INTEGER NOT NULL, 
	price_kind VARCHAR(64) NOT NULL, 
	provider_role VARCHAR(32) NOT NULL, 
	evidence_class VARCHAR(32) NOT NULL, 
	observation_key VARCHAR(64), 
	age_seconds NUMERIC(14, 3), 
	historical_provider_error_pct NUMERIC(14, 8), 
	uncertainty_pct NUMERIC(14, 8), 
	confidence NUMERIC(8, 6), 
	quality_status VARCHAR(32) NOT NULL, 
	state_completeness VARCHAR(32) NOT NULL, 
	is_backfill BOOLEAN NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id), 
	FOREIGN KEY(raw_ingest_id) REFERENCES raw_ingests (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id)
);

CREATE INDEX ix_reference_card_platform_time ON reference_price_observations (card_id, platform, observed_at);

CREATE INDEX ix_reference_price_observations_card_id ON reference_price_observations (card_id);

CREATE INDEX ix_reference_price_observations_evidence_class ON reference_price_observations (evidence_class);

CREATE INDEX ix_reference_price_observations_inserted_at ON reference_price_observations (inserted_at);

CREATE INDEX ix_reference_price_observations_is_backfill ON reference_price_observations (is_backfill);

CREATE INDEX ix_reference_price_observations_market_segment_id ON reference_price_observations (market_segment_id);

CREATE UNIQUE INDEX ix_reference_price_observations_observation_key ON reference_price_observations (observation_key);

CREATE INDEX ix_reference_price_observations_observed_at ON reference_price_observations (observed_at);

CREATE INDEX ix_reference_price_observations_platform ON reference_price_observations (platform);

CREATE INDEX ix_reference_price_observations_price_kind ON reference_price_observations (price_kind);

CREATE INDEX ix_reference_price_observations_provider_role ON reference_price_observations (provider_role);

CREATE INDEX ix_reference_price_observations_provider_timestamp ON reference_price_observations (provider_timestamp);

CREATE INDEX ix_reference_price_observations_quality_status ON reference_price_observations (quality_status);

CREATE INDEX ix_reference_price_observations_source_id ON reference_price_observations (source_id);

CREATE INDEX ix_reference_price_observations_state_completeness ON reference_price_observations (state_completeness);

CREATE TABLE sbc_requirements (
	id UUID NOT NULL, 
	sbc_id UUID NOT NULL, 
	squad_name VARCHAR(160), 
	requirement_type VARCHAR(64) NOT NULL, 
	operator VARCHAR(16), 
	value_numeric NUMERIC(12, 4), 
	value_text VARCHAR(160), 
	payload_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sbc_id) REFERENCES sbcs (id) ON DELETE CASCADE
);

CREATE INDEX ix_sbc_requirements_requirement_type ON sbc_requirements (requirement_type);

CREATE INDEX ix_sbc_requirements_sbc_id ON sbc_requirements (sbc_id);

CREATE INDEX ix_sbc_requirements_value_text ON sbc_requirements (value_text);

CREATE TABLE signals (
	id UUID NOT NULL, 
	generated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	card_id UUID NOT NULL, 
	prediction_id UUID, 
	signal_type VARCHAR(32) NOT NULL, 
	current_pc_price INTEGER NOT NULL, 
	max_buy_price INTEGER NOT NULL, 
	recommended_quantity INTEGER NOT NULL, 
	total_capital_required BIGINT NOT NULL, 
	target_sell_price INTEGER NOT NULL, 
	minimum_sell_price INTEGER NOT NULL, 
	expected_ea_tax INTEGER NOT NULL, 
	expected_net_profit INTEGER NOT NULL, 
	expected_roi NUMERIC(12, 8) NOT NULL, 
	expected_holding_seconds INTEGER NOT NULL, 
	expected_profit_per_hour NUMERIC(20, 6) NOT NULL, 
	liquidity_score NUMERIC(8, 6) NOT NULL, 
	confidence_score NUMERIC(8, 6) NOT NULL, 
	main_catalyst TEXT, 
	historical_analogue TEXT, 
	ea_intervention_risk NUMERIC(8, 6), 
	invalidating_condition TEXT, 
	exit_condition TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(prediction_id) REFERENCES predictions (id)
);

CREATE INDEX ix_signals_card_id ON signals (card_id);

CREATE INDEX ix_signals_generated_at ON signals (generated_at);

CREATE INDEX ix_signals_prediction_id ON signals (prediction_id);

CREATE INDEX ix_signals_signal_type ON signals (signal_type);

CREATE TABLE strategy_performance_snapshots (
	id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	backtest_run_id UUID, 
	game_cycle VARCHAR(32) NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	sample_size INTEGER NOT NULL, 
	acquisition_attempt_sample_size INTEGER NOT NULL, 
	total_net_transfer_profit BIGINT, 
	roi NUMERIC(14, 8), 
	profit_per_hour NUMERIC(20, 6), 
	profit_per_deployed_million NUMERIC(20, 6), 
	capital_turnover NUMERIC(14, 8), 
	hit_rate NUMERIC(8, 6), 
	max_drawdown NUMERIC(14, 8), 
	acquisition_probability NUMERIC(8, 6), 
	profitable_exit_probability NUMERIC(8, 6), 
	median_return_pct NUMERIC(14, 8), 
	median_holding_seconds INTEGER, 
	liquidity_score NUMERIC(8, 6), 
	position_capacity_coins BIGINT, 
	confidence NUMERIC(8, 6), 
	regime_metrics_json JSONB NOT NULL, 
	event_metrics_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE, 
	FOREIGN KEY(backtest_run_id) REFERENCES strategy_backtest_runs (id)
);

CREATE INDEX ix_strategy_perf_strategy_cycle_time ON strategy_performance_snapshots (strategy_id, game_cycle, calculated_at);

CREATE INDEX ix_strategy_performance_snapshots_backtest_run_id ON strategy_performance_snapshots (backtest_run_id);

CREATE INDEX ix_strategy_performance_snapshots_calculated_at ON strategy_performance_snapshots (calculated_at);

CREATE INDEX ix_strategy_performance_snapshots_confidence ON strategy_performance_snapshots (confidence);

CREATE INDEX ix_strategy_performance_snapshots_game_cycle ON strategy_performance_snapshots (game_cycle);

CREATE INDEX ix_strategy_performance_snapshots_platform ON strategy_performance_snapshots (platform);

CREATE INDEX ix_strategy_performance_snapshots_strategy_id ON strategy_performance_snapshots (strategy_id);

CREATE TABLE acquisition_opportunity_observations (
	id BIGSERIAL NOT NULL, 
	card_id UUID NOT NULL, 
	platform VARCHAR(16) NOT NULL, 
	reference_observation_id BIGINT NOT NULL, 
	execution_observation_id BIGINT, 
	search_started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	reference_price INTEGER NOT NULL, 
	listing_price INTEGER, 
	discount_to_reference NUMERIC(12, 8), 
	time_to_opportunity_seconds INTEGER, 
	quantity_available INTEGER, 
	acquired BOOLEAN NOT NULL, 
	context_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(reference_observation_id) REFERENCES reference_price_observations (id), 
	FOREIGN KEY(execution_observation_id) REFERENCES execution_observations (id)
);

CREATE INDEX ix_acquisition_opportunity_observations_acquired ON acquisition_opportunity_observations (acquired);

CREATE INDEX ix_acquisition_opportunity_observations_card_id ON acquisition_opportunity_observations (card_id);

CREATE INDEX ix_acquisition_opportunity_observations_discount_to_reference ON acquisition_opportunity_observations (discount_to_reference);

CREATE INDEX ix_acquisition_opportunity_observations_execution_obser_e798 ON acquisition_opportunity_observations (execution_observation_id);

CREATE INDEX ix_acquisition_opportunity_observations_observed_at ON acquisition_opportunity_observations (observed_at);

CREATE INDEX ix_acquisition_opportunity_observations_platform ON acquisition_opportunity_observations (platform);

CREATE INDEX ix_acquisition_opportunity_observations_reference_obser_7e23 ON acquisition_opportunity_observations (reference_observation_id);

CREATE INDEX ix_acquisition_opportunity_observations_search_started_at ON acquisition_opportunity_observations (search_started_at);

CREATE TABLE community_signals (
	id UUID NOT NULL, 
	content_id UUID NOT NULL, 
	trader_id UUID, 
	card_id UUID, 
	category_key VARCHAR(128), 
	extracted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	direction VARCHAR(24) NOT NULL, 
	quoted_entry INTEGER, 
	target_price INTEGER, 
	catalyst TEXT, 
	horizon_seconds INTEGER, 
	stated_confidence NUMERIC(8, 6), 
	preceded_market_move BOOLEAN, 
	extraction_confidence NUMERIC(8, 6), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(content_id) REFERENCES community_content (id) ON DELETE CASCADE, 
	FOREIGN KEY(trader_id) REFERENCES community_traders (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_community_signals_card_id ON community_signals (card_id);

CREATE INDEX ix_community_signals_category_key ON community_signals (category_key);

CREATE INDEX ix_community_signals_content_id ON community_signals (content_id);

CREATE INDEX ix_community_signals_direction ON community_signals (direction);

CREATE INDEX ix_community_signals_extracted_at ON community_signals (extracted_at);

CREATE INDEX ix_community_signals_horizon_seconds ON community_signals (horizon_seconds);

CREATE INDEX ix_community_signals_preceded_market_move ON community_signals (preceded_market_move);

CREATE INDEX ix_community_signals_trader_id ON community_signals (trader_id);

CREATE TABLE event_impacts (
	id UUID NOT NULL, 
	event_id UUID NOT NULL, 
	card_id UUID, 
	segment_key VARCHAR(160), 
	impact_type VARCHAR(64) NOT NULL, 
	direction VARCHAR(16), 
	confidence NUMERIC(5, 4), 
	reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(event_id) REFERENCES content_events (id) ON DELETE CASCADE, 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_event_impacts_card_id ON event_impacts (card_id);

CREATE INDEX ix_event_impacts_event_id ON event_impacts (event_id);

CREATE INDEX ix_event_impacts_impact_type ON event_impacts (impact_type);

CREATE INDEX ix_event_impacts_segment_key ON event_impacts (segment_key);

CREATE TABLE opportunity_candidates (
	id UUID NOT NULL, 
	card_id UUID NOT NULL, 
	platform VARCHAR(32) NOT NULL, 
	market_segment_id UUID, 
	actionable BOOLEAN NOT NULL, 
	signal_scope VARCHAR(32) NOT NULL, 
	discovered_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_scored_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(32) NOT NULL, 
	rank INTEGER, 
	opportunity_score NUMERIC(16, 8) NOT NULL, 
	reference_observation_id BIGINT, 
	execution_observation_id BIGINT, 
	expected_acquisition_price INTEGER, 
	acquisition_probability NUMERIC(8, 6), 
	expected_discount_to_reference NUMERIC(12, 8), 
	profitable_exit_probability NUMERIC(8, 6), 
	expected_net_profit INTEGER, 
	expected_profit_per_hour NUMERIC(20, 6), 
	expected_holding_seconds INTEGER, 
	position_capacity_coins BIGINT, 
	liquidity_score NUMERIC(8, 6), 
	sell_through_rate NUMERIC(12, 8), 
	volatility NUMERIC(12, 8), 
	downside_risk NUMERIC(12, 8), 
	catalyst_score NUMERIC(8, 6), 
	ea_intervention_risk NUMERIC(8, 6), 
	opportunity_cost NUMERIC(20, 6), 
	requires_manual_verification BOOLEAN NOT NULL, 
	action VARCHAR(32), 
	max_recommended_buy_price INTEGER, 
	target_sell_low INTEGER, 
	target_sell_high INTEGER, 
	recommended_quantity INTEGER, 
	expected_roi NUMERIC(12, 8), 
	confidence_score NUMERIC(8, 6), 
	main_catalyst TEXT, 
	invalidation_condition TEXT, 
	exit_logic TEXT, 
	score_components_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(reference_observation_id) REFERENCES reference_price_observations (id), 
	FOREIGN KEY(execution_observation_id) REFERENCES execution_observations (id)
);

CREATE INDEX ix_opportunity_candidates_action ON opportunity_candidates (action);

CREATE INDEX ix_opportunity_candidates_actionable ON opportunity_candidates (actionable);

CREATE INDEX ix_opportunity_candidates_card_id ON opportunity_candidates (card_id);

CREATE INDEX ix_opportunity_candidates_discovered_at ON opportunity_candidates (discovered_at);

CREATE INDEX ix_opportunity_candidates_execution_observation_id ON opportunity_candidates (execution_observation_id);

CREATE INDEX ix_opportunity_candidates_expires_at ON opportunity_candidates (expires_at);

CREATE INDEX ix_opportunity_candidates_last_scored_at ON opportunity_candidates (last_scored_at);

CREATE INDEX ix_opportunity_candidates_market_segment_id ON opportunity_candidates (market_segment_id);

CREATE INDEX ix_opportunity_candidates_opportunity_score ON opportunity_candidates (opportunity_score);

CREATE INDEX ix_opportunity_candidates_platform ON opportunity_candidates (platform);

CREATE INDEX ix_opportunity_candidates_rank ON opportunity_candidates (rank);

CREATE INDEX ix_opportunity_candidates_reference_observation_id ON opportunity_candidates (reference_observation_id);

CREATE INDEX ix_opportunity_candidates_requires_manual_verification ON opportunity_candidates (requires_manual_verification);

CREATE INDEX ix_opportunity_candidates_signal_scope ON opportunity_candidates (signal_scope);

CREATE INDEX ix_opportunity_candidates_status ON opportunity_candidates (status);

CREATE INDEX ix_opportunity_status_score ON opportunity_candidates (status, opportunity_score, last_scored_at);

CREATE TABLE shadow_orders (
	id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	signal_id UUID, 
	card_id UUID NOT NULL, 
	side VARCHAR(8) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	decision_price INTEGER, 
	limit_price INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	strategy_key VARCHAR(128), 
	reason TEXT, 
	source_snapshot_id BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES shadow_accounts (id), 
	FOREIGN KEY(signal_id) REFERENCES signals (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(source_snapshot_id) REFERENCES market_snapshots (id)
);

CREATE INDEX ix_shadow_orders_account_id ON shadow_orders (account_id);

CREATE INDEX ix_shadow_orders_card_id ON shadow_orders (card_id);

CREATE INDEX ix_shadow_orders_created_at ON shadow_orders (created_at);

CREATE INDEX ix_shadow_orders_side ON shadow_orders (side);

CREATE INDEX ix_shadow_orders_signal_id ON shadow_orders (signal_id);

CREATE INDEX ix_shadow_orders_status ON shadow_orders (status);

CREATE INDEX ix_shadow_orders_strategy_key ON shadow_orders (strategy_key);

CREATE TABLE social_market_impacts (
	id UUID NOT NULL, 
	public_post_id UUID NOT NULL, 
	card_id UUID, 
	measured_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	price_before INTEGER, 
	price_after INTEGER, 
	listing_change_pct NUMERIC(14, 8), 
	liquidity_change_pct NUMERIC(14, 8), 
	abnormal_move_pct NUMERIC(14, 8), 
	reach BIGINT, 
	engagement BIGINT, 
	impact_score NUMERIC(8, 6), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(public_post_id) REFERENCES public_posts (id) ON DELETE CASCADE, 
	FOREIGN KEY(card_id) REFERENCES cards (id)
);

CREATE INDEX ix_social_market_impacts_card_id ON social_market_impacts (card_id);

CREATE INDEX ix_social_market_impacts_impact_score ON social_market_impacts (impact_score);

CREATE INDEX ix_social_market_impacts_measured_at ON social_market_impacts (measured_at);

CREATE INDEX ix_social_market_impacts_public_post_id ON social_market_impacts (public_post_id);

CREATE TABLE activity_feed_items (
	id UUID NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	category VARCHAR(48) NOT NULL, 
	severity VARCHAR(16) NOT NULL, 
	title TEXT NOT NULL, 
	message TEXT, 
	card_id UUID, 
	candidate_id UUID, 
	content_event_id UUID, 
	source_key VARCHAR(64), 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(candidate_id) REFERENCES opportunity_candidates (id), 
	FOREIGN KEY(content_event_id) REFERENCES content_events (id)
);

CREATE INDEX ix_activity_feed_items_candidate_id ON activity_feed_items (candidate_id);

CREATE INDEX ix_activity_feed_items_card_id ON activity_feed_items (card_id);

CREATE INDEX ix_activity_feed_items_category ON activity_feed_items (category);

CREATE INDEX ix_activity_feed_items_content_event_id ON activity_feed_items (content_event_id);

CREATE INDEX ix_activity_feed_items_occurred_at ON activity_feed_items (occurred_at);

CREATE INDEX ix_activity_feed_items_severity ON activity_feed_items (severity);

CREATE INDEX ix_activity_feed_items_source_key ON activity_feed_items (source_key);

CREATE TABLE community_signal_outcomes (
	id UUID NOT NULL, 
	signal_id UUID NOT NULL, 
	evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	directional_correct BOOLEAN, 
	profitable_after_tax BOOLEAN, 
	return_pct NUMERIC(14, 8), 
	benchmark_return_pct NUMERIC(14, 8), 
	alpha_pct NUMERIC(14, 8), 
	max_drawdown_pct NUMERIC(14, 8), 
	timing_quality NUMERIC(8, 6), 
	holding_seconds INTEGER, 
	outcome_status VARCHAR(32) NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(signal_id) REFERENCES community_signals (id) ON DELETE CASCADE
);

CREATE INDEX ix_community_signal_outcomes_evaluated_at ON community_signal_outcomes (evaluated_at);

CREATE INDEX ix_community_signal_outcomes_outcome_status ON community_signal_outcomes (outcome_status);

CREATE UNIQUE INDEX ix_community_signal_outcomes_signal_id ON community_signal_outcomes (signal_id);

CREATE TABLE community_signal_strategy_links (
	id UUID NOT NULL, 
	signal_id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	linked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	match_confidence NUMERIC(8, 6), 
	link_reason TEXT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_community_signal_strategy UNIQUE (signal_id, strategy_id), 
	FOREIGN KEY(signal_id) REFERENCES community_signals (id) ON DELETE CASCADE, 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE
);

CREATE INDEX ix_community_signal_strategy_links_linked_at ON community_signal_strategy_links (linked_at);

CREATE INDEX ix_community_signal_strategy_links_signal_id ON community_signal_strategy_links (signal_id);

CREATE INDEX ix_community_signal_strategy_links_strategy_id ON community_signal_strategy_links (strategy_id);

CREATE TABLE manual_verification_requests (
	id UUID NOT NULL, 
	candidate_id UUID, 
	card_id UUID NOT NULL, 
	platform VARCHAR(32) NOT NULL, 
	market_segment_id UUID, 
	requested_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	priority INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	reason TEXT NOT NULL, 
	reference_observation_id BIGINT, 
	latest_reference_price INTEGER, 
	reference_timestamp TIMESTAMP WITH TIME ZONE, 
	reference_uncertainty_pct NUMERIC(14, 8), 
	expected_acquisition_min INTEGER, 
	expected_acquisition_max INTEGER, 
	attractive_at_or_below INTEGER, 
	required_information TEXT NOT NULL, 
	expected_information_value NUMERIC(20, 6), 
	expires_at TIMESTAMP WITH TIME ZONE, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(candidate_id) REFERENCES opportunity_candidates (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(reference_observation_id) REFERENCES reference_price_observations (id)
);

CREATE INDEX ix_manual_verification_requests_candidate_id ON manual_verification_requests (candidate_id);

CREATE INDEX ix_manual_verification_requests_card_id ON manual_verification_requests (card_id);

CREATE INDEX ix_manual_verification_requests_expires_at ON manual_verification_requests (expires_at);

CREATE INDEX ix_manual_verification_requests_market_segment_id ON manual_verification_requests (market_segment_id);

CREATE INDEX ix_manual_verification_requests_platform ON manual_verification_requests (platform);

CREATE INDEX ix_manual_verification_requests_priority ON manual_verification_requests (priority);

CREATE INDEX ix_manual_verification_requests_reference_observation_id ON manual_verification_requests (reference_observation_id);

CREATE INDEX ix_manual_verification_requests_requested_at ON manual_verification_requests (requested_at);

CREATE INDEX ix_manual_verification_requests_resolved_at ON manual_verification_requests (resolved_at);

CREATE INDEX ix_manual_verification_requests_status ON manual_verification_requests (status);

CREATE TABLE opportunity_strategy_matches (
	id UUID NOT NULL, 
	candidate_id UUID NOT NULL, 
	strategy_id UUID NOT NULL, 
	matched_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	similarity NUMERIC(8, 6) NOT NULL, 
	confidence NUMERIC(8, 6) NOT NULL, 
	historical_sample_size INTEGER NOT NULL, 
	historical_success_rate NUMERIC(8, 6), 
	historical_median_net_return NUMERIC(14, 8), 
	expected_holding_seconds INTEGER, 
	decay_risk NUMERIC(8, 6), 
	current_conditions_differ BOOLEAN NOT NULL, 
	matched_reasons_json JSONB NOT NULL, 
	failure_conditions_json JSONB NOT NULL, 
	features_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_candidate_strategy_match UNIQUE (candidate_id, strategy_id), 
	FOREIGN KEY(candidate_id) REFERENCES opportunity_candidates (id) ON DELETE CASCADE, 
	FOREIGN KEY(strategy_id) REFERENCES strategy_library (id) ON DELETE CASCADE
);

CREATE INDEX ix_opportunity_strategy_matches_candidate_id ON opportunity_strategy_matches (candidate_id);

CREATE INDEX ix_opportunity_strategy_matches_confidence ON opportunity_strategy_matches (confidence);

CREATE INDEX ix_opportunity_strategy_matches_current_conditions_differ ON opportunity_strategy_matches (current_conditions_differ);

CREATE INDEX ix_opportunity_strategy_matches_matched_at ON opportunity_strategy_matches (matched_at);

CREATE INDEX ix_opportunity_strategy_matches_similarity ON opportunity_strategy_matches (similarity);

CREATE INDEX ix_opportunity_strategy_matches_strategy_id ON opportunity_strategy_matches (strategy_id);

CREATE TABLE recommendation_ledger (
	id UUID NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	decision_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	card_id UUID NOT NULL, 
	market_segment_id UUID NOT NULL, 
	candidate_id UUID, 
	action VARCHAR(32) NOT NULL, 
	acquisition_min INTEGER, 
	acquisition_max INTEGER, 
	target_exit_min INTEGER, 
	target_exit_max INTEGER, 
	expected_net_profit BIGINT, 
	expected_holding_seconds INTEGER, 
	confidence NUMERIC(8, 6), 
	available_coin_balance BIGINT, 
	model_version VARCHAR(128), 
	strategy_version VARCHAR(128), 
	input_cutoff_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	evidence_json JSONB NOT NULL, 
	source_observation_ids_json JSONB NOT NULL, 
	user_acted BOOLEAN, 
	execution_transaction_id UUID, 
	outcome_json JSONB NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(candidate_id) REFERENCES opportunity_candidates (id), 
	FOREIGN KEY(execution_transaction_id) REFERENCES portfolio_transactions (id)
);

CREATE INDEX ix_recommendation_ledger_action ON recommendation_ledger (action);

CREATE INDEX ix_recommendation_ledger_candidate_id ON recommendation_ledger (candidate_id);

CREATE INDEX ix_recommendation_ledger_card_id ON recommendation_ledger (card_id);

CREATE INDEX ix_recommendation_ledger_decision_at ON recommendation_ledger (decision_at);

CREATE INDEX ix_recommendation_ledger_execution_transaction_id ON recommendation_ledger (execution_transaction_id);

CREATE INDEX ix_recommendation_ledger_input_cutoff_at ON recommendation_ledger (input_cutoff_at);

CREATE INDEX ix_recommendation_ledger_market_segment_id ON recommendation_ledger (market_segment_id);

CREATE INDEX ix_recommendation_ledger_model_version ON recommendation_ledger (model_version);

CREATE INDEX ix_recommendation_ledger_recorded_at ON recommendation_ledger (recorded_at);

CREATE INDEX ix_recommendation_ledger_strategy_version ON recommendation_ledger (strategy_version);

CREATE INDEX ix_recommendation_ledger_user_acted ON recommendation_ledger (user_acted);

CREATE TABLE shadow_execution_attempts (
	id UUID NOT NULL, 
	order_id UUID, 
	signal_id UUID, 
	card_id UUID NOT NULL, 
	attempted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	reference_observation_id BIGINT, 
	execution_observation_id BIGINT, 
	acquisition_probability NUMERIC(8, 6), 
	expected_acquisition_delay_seconds INTEGER, 
	realized_acquisition_delay_seconds INTEGER, 
	requested_quantity INTEGER NOT NULL, 
	available_quantity INTEGER, 
	filled_quantity INTEGER NOT NULL, 
	signal_quality_score NUMERIC(8, 6), 
	execution_quality_score NUMERIC(8, 6), 
	outcome VARCHAR(32) NOT NULL, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES shadow_orders (id), 
	FOREIGN KEY(signal_id) REFERENCES signals (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(reference_observation_id) REFERENCES reference_price_observations (id), 
	FOREIGN KEY(execution_observation_id) REFERENCES execution_observations (id)
);

CREATE INDEX ix_shadow_execution_attempts_attempted_at ON shadow_execution_attempts (attempted_at);

CREATE INDEX ix_shadow_execution_attempts_card_id ON shadow_execution_attempts (card_id);

CREATE INDEX ix_shadow_execution_attempts_execution_observation_id ON shadow_execution_attempts (execution_observation_id);

CREATE INDEX ix_shadow_execution_attempts_order_id ON shadow_execution_attempts (order_id);

CREATE INDEX ix_shadow_execution_attempts_outcome ON shadow_execution_attempts (outcome);

CREATE INDEX ix_shadow_execution_attempts_reference_observation_id ON shadow_execution_attempts (reference_observation_id);

CREATE INDEX ix_shadow_execution_attempts_signal_id ON shadow_execution_attempts (signal_id);

CREATE TABLE shadow_fills (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	filled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	quantity INTEGER NOT NULL, 
	price INTEGER NOT NULL, 
	ea_tax INTEGER NOT NULL, 
	source_snapshot_id BIGINT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES shadow_orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(source_snapshot_id) REFERENCES market_snapshots (id)
);

CREATE INDEX ix_shadow_fills_filled_at ON shadow_fills (filled_at);

CREATE INDEX ix_shadow_fills_order_id ON shadow_fills (order_id);

CREATE TABLE manual_verification_responses (
	id UUID NOT NULL, 
	request_id UUID NOT NULL, 
	market_segment_id UUID, 
	received_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	listing_prices_json JSONB NOT NULL, 
	lowest_bin INTEGER, 
	best_bid INTEGER, 
	screenshot_uri TEXT, 
	notes TEXT, 
	input_kind VARCHAR(32), 
	observation_confidence NUMERIC(8, 6), 
	observation_age_seconds NUMERIC(14, 3), 
	execution_observation_id BIGINT, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES manual_verification_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(market_segment_id) REFERENCES market_segments (id), 
	FOREIGN KEY(execution_observation_id) REFERENCES execution_observations (id)
);

CREATE INDEX ix_manual_verification_responses_execution_observation_id ON manual_verification_responses (execution_observation_id);

CREATE INDEX ix_manual_verification_responses_input_kind ON manual_verification_responses (input_kind);

CREATE INDEX ix_manual_verification_responses_market_segment_id ON manual_verification_responses (market_segment_id);

CREATE INDEX ix_manual_verification_responses_observed_at ON manual_verification_responses (observed_at);

CREATE INDEX ix_manual_verification_responses_received_at ON manual_verification_responses (received_at);

CREATE INDEX ix_manual_verification_responses_request_id ON manual_verification_responses (request_id);

CREATE TABLE notifications (
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	kind VARCHAR(48) NOT NULL, 
	priority INTEGER NOT NULL, 
	title TEXT NOT NULL, 
	message TEXT, 
	status VARCHAR(24) NOT NULL, 
	card_id UUID, 
	candidate_id UUID, 
	verification_request_id UUID, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	metadata_json JSONB NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(card_id) REFERENCES cards (id), 
	FOREIGN KEY(candidate_id) REFERENCES opportunity_candidates (id), 
	FOREIGN KEY(verification_request_id) REFERENCES manual_verification_requests (id)
);

CREATE INDEX ix_notifications_candidate_id ON notifications (candidate_id);

CREATE INDEX ix_notifications_card_id ON notifications (card_id);

CREATE INDEX ix_notifications_created_at ON notifications (created_at);

CREATE INDEX ix_notifications_expires_at ON notifications (expires_at);

CREATE INDEX ix_notifications_kind ON notifications (kind);

CREATE INDEX ix_notifications_priority ON notifications (priority);

CREATE INDEX ix_notifications_status ON notifications (status);

CREATE INDEX ix_notifications_verification_request_id ON notifications (verification_request_id);
