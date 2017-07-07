#!/usr/bin/env Rscript
LOCATION <- 'auburn university, auburn, alabama' # Location for map;  
PATH <- '/home/lee/git/CT_Project_Dev/HTTP_Server/data/'

working_directory <- sprintf('%s%s', PATH, format(Sys.time(), '%Y-%m-%d'))
setwd(working_directory)

library(ggplot2)
library(ggmap)
library(dplyr)

file_name <- 'table.csv' 
file <- read.csv(file_name, sep = ',') # Gets today's CSV
#head(file)

# Ensures the correct type for each attribute
file$Cell_ID <- as.character(file$Cell_ID)
file$rxl <- as.numeric(file$rxl)
file$lat <- as.numeric(file$lat)
file$lon <- as.numeric(file$lon)

cell_frame = data.frame(file$Cell_ID, file$rxl, file$lon, file$lat)
colnames(cell_frame) = c('Cell_ID', 'rxl', 'lon', 'lat') # creates frame for later

auburn_map <- get_map(location = LOCATION, zoom = 14, scale = 'auto') # Loads map

# Map with all points
map <- ggmap(auburn_map, extent = 'device') + geom_point(data = file, aes(x = lon, y = lat, size = rxl), alpha = 1, size = 3)
png(filename = 'all.png', width=1280, height=1280)
print(map)
dev.off()

towers <- unique(c(as.character(cell_frame$Cell_ID)))
for (tower in towers){
	result <- filter(cell_frame, cell_frame$Cell_ID == tower)
	one <- ggmap(auburn_map, extent = 'device') + geom_point(data = result, aes(x = lon, y = lat, size = rxl), alpha = 1, size = 3)
	png(filename = sprintf('%s.png', tower), width=1280, height=1280)
	print(one)
	dev.off()
}

"
result <- filter(cell_frame, cell_frame$Cell_ID == towers[1])
one <- ggmap(auburn_map, extent = 'device') + geom_point(data = result, aes(x = lon, y = lat, size = rxl), alpha = 1, size = 3)
png(filename = sprintf('%s.png', towers[1]), width=1280, height=1280)
print(one)
dev.off()
"
"+ stat_density2d(data = cell_frame, aes(x = lon, y = lat, fill = ..level.., alpha = ..level..), size = 0.01, bins = 16, geom = 'polygon') 
+ scale_fill_gradient(low = 'green', high = 'red') 
+ scale_alpha(range = c(0, 0.3), guide = FALSE)"
