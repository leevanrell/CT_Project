#!/usr/bin/env Rscript
options(warn=-1) # disables those pesky warnings
args <- commandArgs(TRUE)
LOCATION <- args[1] # Location for map;  
setwd(as.character(args[2]))

library(ggplot2)
library(ggmap)
library(dplyr) # dunno if i'm still using this, filter()?

table_file <- read.csv('table.csv' , sep = ',', colClasses=c('character')) 
table_file$rxl <- as.numeric(table_file$rxl)
table_file$lat <- as.numeric(table_file$lat)
table_file$lon <- as.numeric(table_file$lon)
table_frame = data.frame(table_file$Cell_ID, table_file$rxl, table_file$lon, table_file$lat)
colnames(table_frame) = c('Cell_ID', 'rxl', 'lon', 'lat') 

towers_file <- read.csv('towers.csv', sep = ',', colClasses=c('character')) 
towers_file$lat <- as.numeric(towers_file$lat)
towers_file$lon <- as.numeric(towers_file$lon)
towers_frame = data.frame(towers_file$Cell_ID, towers_file$lon, towers_file$lat)
colnames(towers_frame) = c('Cell_ID', 'lon', 'lat')

auburn_map <- get_map(location = LOCATION, zoom = 10, scale = 'auto') # Loads map
# Creates map w/ all data points
map <- ggmap(auburn_map, extent = 'device') + geom_point(data=towers_frame, aes(lon, lat), size=3, col='blue') + geom_point(data = table_frame, aes(x = lon, y = lat), alpha = 1, size = 2) #+ geom_point(data = towers_frame, aes(x = lon, y = lat, size = 3), alpha = 1, size = 1, col = 'blue')
png(filename = 'all.png', width=960, height=960)
print(map)
dev.off()

auburn_map <- get_map(location = LOCATION, zoom = 14, scale = 'auto') # Loads map (changes zoom)
#towers <- unique(c(as.character(table_frame$Cell_ID)))
towers <- as.character(towers_frame$Cell_ID)
# loops through each tower and creates a png for each
for (tower in towers){
	filtered_table <- filter(table_frame, table_frame$Cell_ID == tower)
	filtered_towers <- filter(towers_frame, towers_frame$Cell_ID == tower)
	one <- ggmap(auburn_map, extent = 'device') + geom_point(data=filtered_towers, aes(lon, lat), size=3, col='blue')
	one <- one + geom_point(data = filtered_table, aes(x = lon, y = lat, size = rxl), alpha = 1, size = 3) + geom_tile(data = table_frame, aes(x = lon, y = lat, alpha = rxl), fill = 'red')
	png(filename = sprintf('%s.png', tower), width=960, height=960)
	print(one)
	dev.off()
}
