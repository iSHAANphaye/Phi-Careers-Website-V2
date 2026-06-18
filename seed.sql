USE phi_careers;

-- Clear existing data (in reverse dependency order)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE applications;
TRUNCATE TABLE job_listings;
TRUNCATE TABLE companies;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Insert Dummy Users
-- All users share the password: password123 (pre-hashed with Werkzeug scrypt)
INSERT INTO users (user_id, name, email, password_hash, role) VALUES
(1, 'Jane Doe', 'jane@candidate.com', 'scrypt:32768:8:1$F6NCe7eMP5abRwer$8423b5f376da6cca62c01d9b54a61bf421723ca9aaa81321a8cefb916eca0bc72e1c90ade2876217b8095648ddad88ee588623e18c284156b4dd2c6419233246', 'candidate'),
(2, 'John Smith', 'john@candidate.com', 'scrypt:32768:8:1$F6NCe7eMP5abRwer$8423b5f376da6cca62c01d9b54a61bf421723ca9aaa81321a8cefb916eca0bc72e1c90ade2876217b8095648ddad88ee588623e18c284156b4dd2c6419233246', 'candidate'),
(3, 'Alice Johnson', 'alice@employer.com', 'scrypt:32768:8:1$F6NCe7eMP5abRwer$8423b5f376da6cca62c01d9b54a61bf421723ca9aaa81321a8cefb916eca0bc72e1c90ade2876217b8095648ddad88ee588623e18c284156b4dd2c6419233246', 'employer'),
(4, 'Bob Williams', 'bob@employer.com', 'scrypt:32768:8:1$F6NCe7eMP5abRwer$8423b5f376da6cca62c01d9b54a61bf421723ca9aaa81321a8cefb916eca0bc72e1c90ade2876217b8095648ddad88ee588623e18c284156b4dd2c6419233246', 'employer');

-- 2. Insert Dummy Companies
INSERT INTO companies (company_id, name, website, description) VALUES
(1, 'Google', 'https://google.com', 'Search engine, web advertisements, cloud computing, and hardware technologies.'),
(2, 'Microsoft', 'https://microsoft.com', 'Global developer of computer software, consumer electronics, and personal computers.'),
(3, 'Stripe', 'https://stripe.com', 'Financial infrastructure platform for payment processing APIs and business software.');

-- 3. Insert Dummy Job Listings
INSERT INTO job_listings (job_id, company_id, title, description, location, salary, status) VALUES
(1, 3, 'Backend Software Engineer', 'We are looking for a Backend Engineer to scale Stripe payment infrastructure. Required skills: Python, SQL, REST APIs, and system design.', 'Remote', 135000.00, 'open'),
(2, 1, 'Frontend UI Engineer', 'Join our Search frontend team to build high-performance user interfaces. Required skills: Javascript, HTML, CSS, React, and browser performance.', 'Chicago, IL', 150000.00, 'open'),
(3, 2, 'Cloud Product Manager', 'Lead product development cycles for Microsoft Azure compute services. Require 3+ years experience, technical background, and excellent communication skills.', 'Redmond, WA', 145000.00, 'open');

-- 4. Insert Dummy Applications
INSERT INTO applications (application_id, user_id, job_id, status, current_step, cover_letter, resume_url, applied_at) VALUES
-- Jane Doe applied to Backend Software Engineer
(1, 1, 1, 'applied', 2, 'Dear Stripe team, I am an experienced backend engineer specialized in RESTful API development and database indexing. I would love to join your team.', 'https://drive.google.com/jane-doe-resume.pdf', CURRENT_TIMESTAMP),
-- John Smith has a draft for Frontend UI Engineer
(2, 2, 2, 'draft', 2, 'Here is my draft application for the frontend position at Google. I have 2 years of React experience.', 'https://drive.google.com/john-smith-resume.pdf', NULL),
-- Jane Doe has a reviewed application for Cloud Product Manager
(3, 1, 3, 'reviewed', 2, 'Hi, I am passionate about Azure services and have managed PM roadmaps in my previous role.', 'https://drive.google.com/jane-doe-resume.pdf', CURRENT_TIMESTAMP);
