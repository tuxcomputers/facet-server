-- Runs only when the container initialises an empty data directory, so it seeds a fresh
-- localdata/postgresdata and never runs again against an existing one.
--
-- Two databases on the one instance: facet is what development runs against, facet_test is
-- what pytest connects to, so a test run cannot drop or rewrite development data.

CREATE DATABASE facet_test OWNER facet;
