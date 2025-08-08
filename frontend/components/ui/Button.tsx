'use client';
import React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';

type Variants = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
type Sizes = 'sm' | 'md' | 'lg';

/**
 * Override 'children' from HTMLMotionProps<'button'> to ensure it's ReactNode only.
 * This avoids the union with MotionValue that Next/TS complains about during build.
 */
interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode;
  variant?: Variants;
  size?: Sizes;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = False,
  icon,
  iconPosition = 'left',
  fullWidth = False,
  className = '',
  disabled,
  type = 'button',
  ...props
}) => {
  const baseClasses = 'btn focus-ring transition-all duration-200 font-medium';
  
  const variantClasses: Record<Variants, string> = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    success: 'btn-success',
    danger: 'btn-danger',
    ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
  };

  const sizeClasses: Record<Sizes, string> = {
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg',
  };

  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    fullWidth ? 'w-full' : '',
    className,
  ].filter(Boolean).join(' ');

  const LoadingSpinner = () => (
    <svg
      className="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  return (
    <motion.button
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      className={classes}
      disabled={Boolean(disabled) || loading}
      type={type}
      {...props}
    >
      {loading && <LoadingSpinner />}
      {!loading && icon && iconPosition === 'left' && (
        <span className="mr-2">{icon}</span>
      )}
      {children as React.ReactNode}
      {!loading && icon && iconPosition === 'right' && (
        <span className="ml-2">{icon}</span>
      )}
    </motion.button>
  );
};

export default Button;
