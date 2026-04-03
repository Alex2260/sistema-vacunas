-- Script de inicialización de la base de datos
CREATE TABLE IF NOT EXISTS pacientes (
    curp VARCHAR(18) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    email VARCHAR(200),
    telefono VARCHAR(15),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vacunas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    dosis_total INT DEFAULT 1,
    intervalo_dias INT DEFAULT 0,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS aplicaciones (
    id SERIAL PRIMARY KEY,
    curp VARCHAR(18) REFERENCES pacientes(curp),
    vacuna_id INT REFERENCES vacunas(id),
    fecha_aplicacion DATE DEFAULT CURRENT_DATE,
    numero_dosis INT DEFAULT 1,
    centro_salud VARCHAR(200),
    lote VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    curp VARCHAR(18) REFERENCES pacientes(curp),
    vacuna_id INT REFERENCES vacunas(id),
    fecha_programada DATE NOT NULL,
    enviada BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Catálogo inicial de vacunas
INSERT INTO vacunas (nombre, dosis_total, intervalo_dias, descripcion) VALUES
('BCG (Tuberculosis)', 1, 0, 'Vacuna contra la tuberculosis, una sola dosis al nacer'),
('Hepatitis B', 3, 30, 'Esquema de 3 dosis: 0, 1 y 6 meses'),
('Pentavalente', 5, 60, 'Difteria, tos ferina, tétanos, polio y Hib - 5 dosis'),
('Rotavirus', 2, 60, 'Previene diarrea grave por rotavirus - 2 dosis'),
('Neumocócica', 3, 60, 'Previene neumonía y meningitis - 3 dosis'),
('Triple Viral SRP', 2, 365, 'Sarampión, Rubéola y Parotiditis - 2 dosis'),
('Varicela', 2, 90, 'Previene varicela - 2 dosis'),
('Influenza', 1, 365, 'Anual - una dosis cada año'),
('COVID-19', 2, 21, 'Esquema básico de 2 dosis + refuerzo anual'),
('VPH (Virus Papiloma Humano)', 2, 180, 'Previene cáncer cervicouterino - 2 dosis')
ON CONFLICT DO NOTHING;
