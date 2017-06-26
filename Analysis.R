

library(ggplot2)
library(ggmap)
library(RJDBC)
drv <- JDBC("org.apache.cassandra.cql.jdbc.CassandraDriver", 
          list.files("/home/lee/apache-cassandra-3.0.14/lib",
          pattern="jar$",full.names=T))



conn <- dbConnect(drv, "jdbc:cassandra://localhost:9042/auresearch/DetectorData")