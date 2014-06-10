-- This script is used to convert an elections database from the version 0.x
-- to the version 2.x.
-- There was some changes made to the model during the rewrite to flask (v2.x)
-- and this allows to convert from v1 to v2.

ALTER TABLE elections ADD COLUMN voting_type VARCHAR(100) NOT NULL DEFAULT 'range';

-- ALTER TABLE elections ADD COLUMN candidates_are_fasusers BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE elections ADD COLUMN fas_user VARCHAR(50);

ALTER TABLE votes RENAME COLUMN weight TO value;

ALTER TABLE elections DROP COLUMN votes_per_user;


-- ALTER TABLE elections RENAME COLUMN shortdesc TO summary;


-- For 2.1
ALTER TABLE elections DROP COLUMN candidates_are_fasusers;

ALTER TABLE elections RENAME COLUMN usefas TO candidates_are_fasusers;

ALTER TABLE elections ALTER COLUMN candidates_are_fasusers TYPE integer;
