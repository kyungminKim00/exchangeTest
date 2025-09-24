-- Initialize Alt Exchange Database
-- Database is already created by POSTGRES_DB environment variable

-- Create custom types
CREATE TYPE account_status AS ENUM ('active', 'suspended', 'closed');
CREATE TYPE asset_type AS ENUM ('ALT', 'USDT', 'BTC', 'ETH');
CREATE TYPE order_side AS ENUM ('buy', 'sell');
CREATE TYPE order_type AS ENUM ('limit', 'market', 'stop', 'stop_limit');
CREATE TYPE time_in_force AS ENUM ('GTC', 'IOC', 'FOK');
CREATE TYPE order_status AS ENUM ('open', 'partial', 'filled', 'canceled', 'rejected');
CREATE TYPE transaction_type AS ENUM ('deposit', 'withdrawal', 'fee', 'transfer');
CREATE TYPE transaction_status AS ENUM ('pending', 'confirmed', 'failed', 'cancelled');

-- Create tables for the exchange
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status account_status DEFAULT 'active',
    kyc_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);

CREATE TABLE IF NOT EXISTS balances (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    asset asset_type NOT NULL,
    available NUMERIC(36, 18) DEFAULT 0,
    locked NUMERIC(36, 18) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, asset)
);

CREATE INDEX IF NOT EXISTS idx_balances_account_id ON balances(account_id);
CREATE INDEX IF NOT EXISTS idx_balances_asset ON balances(asset);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    market VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    type order_type NOT NULL,
    time_in_force time_in_force NOT NULL,
    price NUMERIC(36, 18),
    amount NUMERIC(36, 18) NOT NULL,
    filled NUMERIC(36, 18) DEFAULT 0,
    status order_status DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_account_id ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_market ON orders(market);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    buy_order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sell_order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    maker_order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    taker_order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    taker_side order_side NOT NULL,
    price NUMERIC(36, 18) NOT NULL,
    amount NUMERIC(36, 18) NOT NULL,
    fee NUMERIC(36, 18) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_buy_order_id ON trades(buy_order_id);
CREATE INDEX IF NOT EXISTS idx_trades_sell_order_id ON trades(sell_order_id);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tx_hash VARCHAR(255) UNIQUE,
    chain VARCHAR(50) NOT NULL,
    asset asset_type NOT NULL,
    type transaction_type NOT NULL,
    status transaction_status NOT NULL,
    confirmations INTEGER DEFAULT 0,
    amount NUMERIC(36, 18) NOT NULL,
    address VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_tx_hash ON transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    metadata TEXT, -- JSON string
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create sequences for ID generation
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS accounts_id_seq;
CREATE SEQUENCE IF NOT EXISTS balances_id_seq;
CREATE SEQUENCE IF NOT EXISTS orders_id_seq;
CREATE SEQUENCE IF NOT EXISTS trades_id_seq;
CREATE SEQUENCE IF NOT EXISTS transactions_id_seq;
CREATE SEQUENCE IF NOT EXISTS audit_logs_id_seq;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO alt_exchange_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO alt_exchange_user;