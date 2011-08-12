drop view electionvotes;
drop view fvotecount;
drop view votecount;
drop view uservotes;

drop table votes;
drop table legalvoters;
drop table candidates;
drop table elections;

CREATE TABLE elections (
    id serial NOT NULL,
-- was shortname
    shortdesc text NOT NULL,
-- was name
    alias text NOT NULL,
-- was info
    description text NOT NULL,
    url text NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
-- was max_seats
    seats_elected integer NOT NULL,
    votes_per_user integer NOT NULL,
    embargoed integer default 0 NOT NULL,
    usefas integer default 0 NOT NULL,
    allow_nominations integer default 0 NOT NULL,
    nominations_until timestamp without time zone,
    unique (shortdesc),
    primary key (id)
);

CREATE TABLE candidates (
    id serial,
    election_id integer NOT NULL,
    name text NOT NULL,
    url text,
    formalname text,
    human integer,
    status integer,
    foreign key (election_id) references elections (id),
    unique (id),
    primary key (id, election_id)
);

CREATE TABLE legalvoters (
    id serial,
    election_id integer not null,
    group_name text not null,
    foreign key (election_id) references elections (id),
    primary key (id)
);

CREATE TABLE electionadmins (
    id serial,
    election_id integer not null,
    group_name text not null,
    foreign key (election_id) references elections (id),
    primary key (id)
);

CREATE TABLE votes (
    id serial,
    voter text NOT NULL,
    timestamp timestamp without time zone  NOT NULL,
    candidate_id integer NOT NULL,
    weight integer NOT NULL,
    election_id integer NOT NULL,
    foreign key (candidate_id) references candidates(id),
    foreign key (election_id) references elections(id),
    primary key (id)
);


CREATE VIEW electionvotes AS
    SELECT votes.election_id, count(votes.election_id) AS novotes FROM votes GROUP BY votes.election_id;




CREATE VIEW votecount AS
    SELECT votes.candidate_id, votes.election_id, sum(votes.weight) AS novotes FROM votes GROUP BY votes.candidate_id, votes.election_id ORDER BY sum(votes.weight) DESC;


CREATE VIEW fvotecount AS
    SELECT c.id, c.name, v.election_id, v.novotes FROM votecount v, candidates c WHERE (c.id = v.candidate_id) ORDER BY v.novotes DESC;


CREATE VIEW uservotes AS
    SELECT votes.election_id, votes.voter, count(votes.voter) AS novotes FROM votes GROUP BY votes.election_id, votes.voter;
