-- Query final para criar o usuário super admin com hash correto
-- Execute esta query no BigQuery

-- Primeiro, delete o usuário existente (se houver)
DELETE FROM `trivihair.finaflow.Users` 
WHERE username = 'admin';

-- Depois, insira o usuário com hash correto
INSERT INTO `trivihair.finaflow.Users` 
(id, username, email, hashed_password, role, tenant_id, created_at)
VALUES 
(
  GENERATE_UUID(),
  'admin',
  'admin@finaflow.com',
  '$2b$12$xXL9OxVMhmVScs6RRZ8IO.PIaaX6Uq8egGw9SboJ.1.kC7nM714re',
  'super_admin',
  NULL,
  CURRENT_TIMESTAMP()
);

-- Verifique se foi criado corretamente
SELECT username, email, role, created_at 
FROM `trivihair.finaflow.Users` 
WHERE username = 'admin';
