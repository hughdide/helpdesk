-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 15-06-2026 a las 11:46:46
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `helpdesk`
--
CREATE DATABASE IF NOT EXISTS `helpdesk` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `helpdesk`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categorias`
--

DROP TABLE IF EXISTS `categorias`;
CREATE TABLE IF NOT EXISTS `categorias` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categorias_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `categorias`
--

INSERT INTO `categorias` (`id`, `nombre`) VALUES
(1, 'General'),
(2, 'Hardware'),
(4, 'Red'),
(3, 'Software');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notificaciones`
--

DROP TABLE IF EXISTS `notificaciones`;
CREATE TABLE IF NOT EXISTS `notificaciones` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ticket_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `email` varchar(190) DEFAULT NULL,
  `tipo` varchar(80) DEFAULT NULL,
  `asunto` varchar(255) DEFAULT NULL,
  `cuerpo` text DEFAULT NULL,
  `enviado` tinyint(1) NOT NULL DEFAULT 0,
  `error_msg` varchar(255) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_notif_ticket` (`ticket_id`),
  KEY `idx_notif_usuario` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tickets`
--

DROP TABLE IF EXISTS `tickets`;
CREATE TABLE IF NOT EXISTS `tickets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(255) NOT NULL,
  `descripcion` text NOT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'Abierto',
  `prioridad` varchar(20) NOT NULL DEFAULT 'media',
  `archivo` varchar(255) DEFAULT NULL,
  `archivo_blob` longblob DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `agente_id` int(11) DEFAULT NULL,
  `categoria_id` int(11) DEFAULT NULL,
  `cerrado_en` datetime DEFAULT NULL,
  `sla_respuesta_limite` datetime DEFAULT NULL,
  `sla_resolucion_limite` datetime DEFAULT NULL,
  `primera_respuesta_en` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_tickets_usuario` (`usuario_id`),
  KEY `idx_tickets_agente` (`agente_id`),
  KEY `idx_tickets_categoria` (`categoria_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ticket_historial`
--

DROP TABLE IF EXISTS `ticket_historial`;
CREATE TABLE IF NOT EXISTS `ticket_historial` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ticket_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `detalle` text NOT NULL,
  `es_interno` tinyint(1) NOT NULL DEFAULT 0,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_hist_ticket` (`ticket_id`),
  KEY `idx_hist_usuario` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  `email` varchar(190) NOT NULL,
  `password` varchar(512) NOT NULL,
  `rol` varchar(20) NOT NULL DEFAULT 'cliente',
  `reset_token` varchar(64) DEFAULT NULL,
  `reset_token_expira` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `email`, `password`, `rol`, `reset_token`, `reset_token_expira`) VALUES
(1, 'Sara', 'sara.b@galsoft.es', 'scrypt:32768:8:1$Z91PnWv7tOEZW2Vs$5bbf2efe2c950d2d9935ca405c2107e2eb3b7659894a39589012729c9e031c92ca59cb4a8736e155625df980f9e83e08b49c802f9cab188116d173eeb4917163', 'admin', NULL, NULL),
(2, 'Beatriz Patiño', 'beatriz.p@galsoft.es', 'scrypt:32768:8:1$RmSp2BngcMCg03P1$06f7f05054151c175cac3cda12ffa7074f68a145414a16f54382eddf93088ca29bd31b67c81a8299c3106f59d4d0846282d723079e21edfef6b67bfebc6fc1a1', 'agente', NULL, NULL),
(3, 'Elizabeth Martínez', 'elizabeth.m@galsoft.es', 'scrypt:32768:8:1$AcU2y9AmtCIjQMWg$b9c7e63b34498cfbb951091ad655f14e26d4d4372e5caec6c2dd5430d4323e98284b786e205f62c0db445e59a7901788c4036c3bb445d2ef2ebe2fd1bf4b5d30', 'agente', NULL, NULL),
(4, 'Bea', 'beapatinoalende@gmail.com', 'scrypt:32768:8:1$XiYstUD0gsPwmyaA$e53f6d3d1ae26a5dcb297ae54fd19ecfd550eb0d1cbe3e7e990f16bf78f9fa8c156bca9445fe151f050c622fe4b85f55564cc9ba6f0208aaea1f69f9e5fba45e', 'cliente', NULL, NULL);

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `notificaciones`
--
ALTER TABLE `notificaciones`
  ADD CONSTRAINT `fk_notif_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_notif_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Filtros para la tabla `tickets`
--
ALTER TABLE `tickets`
  ADD CONSTRAINT `fk_tickets_agente` FOREIGN KEY (`agente_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_tickets_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_tickets_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `ticket_historial`
--
ALTER TABLE `ticket_historial`
  ADD CONSTRAINT `fk_hist_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_hist_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
