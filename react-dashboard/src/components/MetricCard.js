import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';

function MetricCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary', 
  trend = null 
}) {
  const theme = useTheme();

  const getColorValue = (colorName) => {
    switch (colorName) {
      case 'success':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return '#f57c00';
      case 'primary':
      default:
        return theme.palette.primary.main;
    }
  };

  const getTrendIcon = () => {
    if (trend === null || trend === undefined) return null;

    if (trend > 0) {
      return <TrendingUp sx={{ fontSize: 16, color: theme.palette.success.main }} />;
    } else if (trend < 0) {
      return <TrendingDown sx={{ fontSize: 16, color: theme.palette.error.main }} />;
    }
    return null;
  };

  const getTrendColor = () => {
    if (trend === null || trend === undefined) return theme.palette.text.secondary;
    return trend >= 0 ? theme.palette.success.main : theme.palette.error.main;
  };

  return (
    <Card
      className="metric-card"
      sx={{
        height: '100%',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
        border: `2px solid ${getColorValue(color)}20`,
        borderLeft: `4px solid ${getColorValue(color)}`,
        '&:hover': {
          borderColor: `${getColorValue(color)}40`,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: 0.8,
              fontSize: '0.75rem',
            }}
          >
            {title}
          </Typography>
          <Box sx={{ color: getColorValue(color), opacity: 0.7 }}>
            {icon}
          </Box>
        </Box>

        {/* Main Value */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              lineHeight: 1.1,
              mb: 1,
              fontSize: '2rem',
            }}
          >
            {value}
          </Typography>

          {/* Subtitle with trend */}
          {subtitle && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Typography
                variant="body2"
                sx={{
                  color: getTrendColor(),
                  fontWeight: 600,
                  fontSize: '0.875rem',
                }}
              >
                {subtitle}
              </Typography>
              {getTrendIcon()}
            </Box>
          )}
        </Box>

        {/* Live indicator for real-time metrics */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: getColorValue(color),
              opacity: 0.6,
              animation: 'pulse 3s infinite',
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
}

export default MetricCard;
