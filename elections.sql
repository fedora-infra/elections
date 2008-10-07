drop table if exists votes;
drop table if exists candidates;
drop table if exists legalvoters;
drop table if exists elections;
drop view if exists votecount;
drop view if exists fvotecount;
drop view if exists uservotes;

CREATE TABLE elections (
id integer NOT NULL auto_increment,
-- Old 'shortname'
alias varchar(50) NOT NULL,
-- Numerical value, specifying what stage the election is in
status tinyint NOT NULL,
-- Numerical value, specifying what voting method is used
method tinyint NOT NULL,

shortdesc text NOT NULL,
description text NOT NULL,

url text,
start_date timestamp DEFAULT 0 NOT NULL,
end_date timestamp DEFAULT 0 NOT NULL,
-- Are results currently embargoed?
embargoed boolean NOT NULL,
-- Number of seats elected
seats_elected integer NOT NULL,
-- Does this election support nominations?
allow_nominations boolean NOT NULL,
-- If so, when do they have to be in by?
nomination_end timestamp DEFAULT 0,
-- Do we use FAS for candidate names?
usefas boolean NOT NULL,
UNIQUE (alias),
PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE legalvoters (
id integer NOT NULL auto_increment,
election_id integer NOT NULL,
type integer NOT NULL,
group_name text NOT NULL,
FOREIGN KEY (election_id) references elections (id),
INDEX (election_id, type),
PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE candidates (
id integer NOT NULL auto_increment,
election_id integer NOT NULL,
-- Numerical value, specifying candidates' "status"
status tinyint NOT NULL,
name text NOT NULL,
url text,
blurb text,
nominated_by text,
FOREIGN KEY (election_id) references elections (id),
PRIMARY KEY (id, election_id)
) ENGINE=InnoDB;

CREATE TABLE votes (
id integer NOT NULL auto_increment,
voter text NOT NULL,
candidate_id integer NOT NULL,
weight integer NOT NULL,
election_id integer NOT NULL,
-- unique(voter_id, candidate_id, election_id),
FOREIGN KEY (candidate_id) references candidates (id),
FOREIGN KEY (election_id) references elections (id),
PRIMARY KEY (id)
) ENGINE=InnoDB;

#CREATE TABLE questions (
#
#) ENGINE=InnoDB;

create view votecount as select candidate_id, election_id, sum(weight) as novotes from votes group by candidate_id, election_id order by novotes desc;

create view fvotecount as select c.id, c.name, v.election_id, v.novotes from votecount v, candidates c where c.id = v.candidate_id order by novotes desc;

create view uservotes as select election_id, voter, count(voter) as novotes from votes group by election_id, voter;
